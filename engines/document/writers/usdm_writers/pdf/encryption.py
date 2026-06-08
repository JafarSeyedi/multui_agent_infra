"""
PDF Encryption module - Professional and complete implementation
Supports PDF encryption standards 1.4 through 2.0
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass
from enum import Enum
from enum import IntFlag
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import modes


class EncryptionAlgorithm(Enum):
    """PDF encryption algorithms"""
    RC4_40 = "RC4_40"      # PDF 1.2 - RC4 with 40-bit key
    RC4_128 = "RC4_128"    # PDF 1.4 - RC4 with 128-bit key
    AES_128 = "AES_128"    # PDF 1.6 - AES with 128-bit key (CBC)
    AES_256 = "AES_256"    # PDF 2.0 - AES with 256-bit key (CBC)


class PermissionFlag(IntFlag):
    """PDF access permission flags (according to ISO 32000 standard)"""
    # Low-order 12 bits (bits 0-11) are reserved
    PRINT = 1 << 2          # (Revision 2) Print the document
    MODIFY = 1 << 3         # (Revision 2) Modify the contents
    COPY = 1 << 4           # (Revision 2) Copy or extract text and graphics
    ANNOTATE = 1 << 5       # (Revision 2) Add or modify annotations
    FORM_FILL = 1 << 8      # (Revision 3) Fill in form fields
    EXTRACT = 1 << 9        # (Revision 3) Extract text and graphics
    ASSEMBLE = 1 << 10      # (Revision 3) Assemble the document
    PRINT_HIGH = 1 << 11    # (Revision 3) Print high quality

    # PDF 2.0 additional permissions
    MODIFY_ANNOTATIONS = 1 << 12   # Modify annotations
    FILL_FORM = 1 << 13            # Fill in existing form fields
    ACCESSIBILITY = 1 << 14        # Extract for accessibility
    DOCUMENT_ASSEMBLY = 1 << 15    # Document assembly


@dataclass
class EncryptionOptions:
    """PDF encryption options"""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256
    user_password: str = ""          # User password
    owner_password: str = ""          # Owner password
    permissions: int = 0              # Permissions (bit flags)
    metadata_encrypted: bool = True   # Encrypt metadata
    encrypt_attachments: bool = True  # Encrypt attachments (PDF 2.0)
    encrypt_form_data: bool = True     # Encrypt form data
    key_length: int = 256             # Key length (bits)
    revision: int = 5                  # Encryption revision (2-5)

    def __post_init__(self):
        """Validation and setting default values"""
        # Set owner password if not specified
        if not self.owner_password and self.user_password:
            self.owner_password = self._generate_owner_password(self.user_password)
        elif not self.owner_password:
            self.owner_password = secrets.token_urlsafe(32)

        # Set default permissions
        if self.permissions == 0:
            self.permissions = (
                PermissionFlag.PRINT.value |
                PermissionFlag.COPY.value |
                PermissionFlag.ANNOTATE.value |
                PermissionFlag.FORM_FILL.value |
                PermissionFlag.EXTRACT.value |
                PermissionFlag.ACCESSIBILITY.value
            )

        # Set key length based on algorithm
        if self.algorithm == EncryptionAlgorithm.RC4_40:
            self.key_length = 40
            self.revision = 2
        elif self.algorithm == EncryptionAlgorithm.RC4_128:
            self.key_length = 128
            self.revision = 3
        elif self.algorithm == EncryptionAlgorithm.AES_128:
            self.key_length = 128
            self.revision = 4
        elif self.algorithm == EncryptionAlgorithm.AES_256:
            self.key_length = 256
            self.revision = 5

        # Key length validation
        valid_lengths = {40, 128, 256}
        if self.key_length not in valid_lengths:
            raise ValueError(f"Invalid key length: {self.key_length}. Allowed values: {valid_lengths}")

    @staticmethod
    def _generate_owner_password(user_password: str) -> str:
        """Generate owner password from user password"""
        salt = secrets.token_bytes(16)
        combined = user_password.encode('utf-8') + salt
        hash_obj = hashlib.sha256(combined)
        return base64.urlsafe_b64encode(hash_obj.digest()[:24]).decode('utf-8')


class PDFEncryptor:
    """Professional PDF encryptor with full standards support"""

    # PDF standard constants
    PADDING_STRING = bytes([
        0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41,
        0x64, 0x00, 0x4E, 0x56, 0xFF, 0xFA, 0x01, 0x08,
        0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
        0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A
    ])

    def __init__(self, options: EncryptionOptions):
        self.options = options
        self.encryption_key: bytes | None = None
        self.encryption_dict: dict[str, Any] | None = None
        self.file_id: bytes | None = None
        self._backend = default_backend()

        # Store intermediate keys
        self._o_key: bytes | None = None
        self._u_key: bytes | None = None
        self._ue_key: bytes | None = None
        self._oe_key: bytes | None = None
        self._perms_key: bytes | None = None

    def generate_encryption_key(self, file_id: bytes) -> bytes:
        """Generate main encryption key based on PDF standard"""
        self.file_id = file_id

        if self.options.revision == 5:
            # SHA-256 algorithm for PDF 2.0
            return self._generate_key_revision_5()
        elif self.options.revision == 4:
            # AES-128 algorithm for PDF 1.7 ExtensionLevel 3
            return self._generate_key_revision_4()
        elif self.options.revision == 3:
            # RC4-128 algorithm for PDF 1.4
            return self._generate_key_revision_3()
        elif self.options.revision == 2:
            # RC4-40 algorithm for PDF 1.2
            return self._generate_key_revision_2()
        else:
            raise ValueError(f"Invalid encryption revision: {self.options.revision}")

    def _generate_key_revision_5(self) -> bytes:
        """Generate key for Revision 5 (AES-256) encryption"""
        # 1. Generate salts
        user_salt = secrets.token_bytes(8)
        owner_salt = secrets.token_bytes(8)
        secrets.token_bytes(8)
        secrets.token_bytes(8)

        # 2. Compute user key (U)
        user_password = self._pad_password(self.options.user_password.encode('utf-8'))
        user_hash = hashlib.sha256(user_password + user_salt).digest()

        # 3. Compute owner key (O)
        owner_password = self._pad_password(self.options.owner_password.encode('utf-8'))
        owner_hash = hashlib.sha256(owner_password + owner_salt + user_hash).digest()

        # 4. Generate encryption key (Encryption Key)
        encryption_key = secrets.token_bytes(32)  # 256-bit key

        # 5. Encrypt key for user (UE)
        iv_user = secrets.token_bytes(16)
        cipher_user = Cipher(
            algorithms.AES(encryption_key),
            modes.CBC(iv_user),
            backend=self._backend
        )
        encryptor_user = cipher_user.encryptor()
        padded_user_key = self._pad_aes(user_hash[:32])
        ue_key = iv_user + encryptor_user.update(padded_user_key) + encryptor_user.finalize()

        # 6. Encrypt key for owner (OE)
        iv_owner = secrets.token_bytes(16)
        cipher_owner = Cipher(
            algorithms.AES(encryption_key),
            modes.CBC(iv_owner),
            backend=self._backend
        )
        encryptor_owner = cipher_owner.encryptor()
        padded_owner_key = self._pad_aes(owner_hash[:32])
        oe_key = iv_owner + encryptor_owner.update(padded_owner_key) + encryptor_owner.finalize()

        # 7. Compute permissions (Perms)
        perms = struct.pack('<I', self.options.permissions)
        perms += b'T' if self.options.metadata_encrypted else b'F'
        perms += b'adb'  # Additional bytes for PDF 2.0
        perms += secrets.token_bytes(4)  # Padding

        # Encrypt permissions
        iv_perms = secrets.token_bytes(16)
        cipher_perms = Cipher(
            algorithms.AES(encryption_key),
            modes.CBC(iv_perms),
            backend=self._backend
        )
        encryptor_perms = cipher_perms.encryptor()
        padded_perms = self._pad_aes(perms)
        encrypted_perms = iv_perms + encryptor_perms.update(padded_perms) + encryptor_perms.finalize()

        # Store intermediate keys
        self._u_key = user_hash
        self._o_key = owner_hash
        self._ue_key = ue_key
        self._oe_key = oe_key
        self._perms_key = encrypted_perms

        self.encryption_key = encryption_key
        return encryption_key

    def _generate_key_revision_4(self) -> bytes:
        """Generate key for Revision 4 (AES-128) encryption"""
        file_id = self.file_id
        if file_id is None:
            raise ValueError("file_id must be set before generating an encryption key.")

        # 1. Pad passwords
        user_password = self._pad_password(self.options.user_password.encode('utf-8'))
        owner_password = self._pad_password(self.options.owner_password.encode('utf-8'))

        # 2. Compute encryption key (Algorithm 2)
        key = self._compute_encryption_key_r4(
            user_password,
            owner_password,
            self.options.permissions,
            file_id
        )

        # 3. Compute O value (Algorithm 3)
        o_value = self._compute_o_value_r4(owner_password, user_password, key)

        # 4. Compute U value (Algorithm 4)
        u_value = self._compute_u_value_r4(user_password, key)

        # 5. Compute encryption dictionary
        self._o_key = o_value
        self._u_key = u_value

        self.encryption_key = key
        return key

    def _generate_key_revision_3(self) -> bytes:
        """Generate key for Revision 3 (RC4-128) encryption"""
        file_id = self.file_id
        if file_id is None:
            raise ValueError("file_id must be set before generating an encryption key.")

        # 1. Pad passwords
        user_password = self._pad_password(self.options.user_password.encode('utf-8'))
        owner_password = self._pad_password(self.options.owner_password.encode('utf-8'))

        # 2. Compute encryption key (Algorithm 2)
        key = self._compute_encryption_key_r3(
            user_password,
            owner_password,
            self.options.permissions,
            file_id
        )

        # 3. Compute O value (Algorithm 3)
        o_value = self._compute_o_value_r3(owner_password, user_password, key)

        # 4. Compute U value (Algorithm 4)
        u_value = self._compute_u_value_r3(user_password, key)

        # 5. Compute encryption dictionary
        self._o_key = o_value
        self._u_key = u_value

        self.encryption_key = key
        return key

    def _generate_key_revision_2(self) -> bytes:
        """Generate key for Revision 2 (RC4-40) encryption"""
        file_id = self.file_id
        if file_id is None:
            raise ValueError("file_id must be set before generating an encryption key.")

        # Similar to revision 3 but with 40-bit key
        user_password = self._pad_password(self.options.user_password.encode('utf-8'))
        owner_password = self._pad_password(self.options.owner_password.encode('utf-8'))

        # Generate 40-bit key (5 bytes)
        key = self._compute_encryption_key_r2(
            user_password,
            owner_password,
            self.options.permissions,
            file_id
        )

        # Compute O and U values
        o_value = self._compute_o_value_r2(owner_password, user_password, key)
        u_value = self._compute_u_value_r2(user_password, key)

        self._o_key = o_value
        self._u_key = u_value

        self.encryption_key = key
        return key

    def _compute_encryption_key_r4(self, user_pass: bytes, owner_pass: bytes,
                                  permissions: int, file_id: bytes) -> bytes:
        """Compute encryption key for Revision 4"""
        # Algorithm 2 from PDF 1.7 ExtensionLevel 3
        key_length = self.options.key_length // 8

        # Step 1: Pad passwords
        padded_user = self._pad_password_32(user_pass)
        padded_owner = self._pad_password_32(owner_pass)

        # Step 2: Compute hash
        hash_input = (
            padded_user +
            padded_owner +
            struct.pack('<I', permissions) +
            file_id +
            b'\xFF\xFF\xFF\xFF'  # Metadata flag
        )

        # Step 3: Iterate 64 times
        key = hashlib.md5(hash_input).digest()
        for i in range(1, 64):
            key = hashlib.md5(key + hash_input).digest()

        # Step 4: Truncate to key length
        return key[:key_length]

    def _compute_encryption_key_r3(self, user_pass: bytes, owner_pass: bytes,
                                  permissions: int, file_id: bytes) -> bytes:
        """Compute encryption key for Revision 3"""
        # Algorithm 2 from PDF 1.4
        key_length = 16  # 128-bit for RC4-128

        # Pad passwords
        padded_user = self._pad_password_32(user_pass)
        padded_owner = self._pad_password_32(owner_pass)

        # Compute hash
        hash_input = (
            padded_user +
            padded_owner +
            struct.pack('<I', permissions) +
            file_id
        )

        key = hashlib.md5(hash_input).digest()

        # Iterate 50 times
        for i in range(1, 50):
            key = hashlib.md5(key[:key_length]).digest()

        return key[:key_length]

    def _compute_encryption_key_r2(self, user_pass: bytes, owner_pass: bytes,
                                  permissions: int, file_id: bytes) -> bytes:
        """Compute encryption key for Revision 2"""
        key_length = 5  # 40-bit for RC4-40

        # Similar to R3 but with 40-bit key
        padded_user = self._pad_password_32(user_pass)
        padded_owner = self._pad_password_32(owner_pass)

        hash_input = (
            padded_user +
            padded_owner +
            struct.pack('<I', permissions) +
            file_id
        )

        key = hashlib.md5(hash_input).digest()

        # Iterate 50 times
        for i in range(1, 50):
            key = hashlib.md5(key[:key_length]).digest()

        return key[:key_length]

    def _compute_o_value_r4(self, owner_pass: bytes, user_pass: bytes, key: bytes) -> bytes:
        """Compute O value for Revision 4"""
        # Algorithm 3 for AES-128
        padded_owner = self._pad_password_32(owner_pass)
        padded_user = self._pad_password_32(user_pass)

        # Hash owner password with user password
        hash_input = padded_owner + padded_user
        hash_result = hashlib.md5(hash_input).digest()

        # Iterate 20 times
        for i in range(1, 20):
            xor_key = bytes([b ^ i for b in key])
            hash_result = hashlib.md5(xor_key + hash_result).digest()

        return hash_result[:32]

    def _compute_o_value_r3(self, owner_pass: bytes, user_pass: bytes, key: bytes) -> bytes:
        """Compute O value for Revision 3"""
        padded_owner = self._pad_password_32(owner_pass)
        self._pad_password_32(user_pass)

        # MD5 hash
        hash_result = hashlib.md5(padded_owner).digest()

        # RC4 encryption with key
        encrypted = self._rc4_encrypt(hash_result, key)

        # Iterate 19 times
        for i in range(1, 20):
            new_key = bytes([b ^ i for b in key])
            encrypted = self._rc4_encrypt(encrypted, new_key)

        return encrypted

    def _compute_o_value_r2(self, owner_pass: bytes, user_pass: bytes, key: bytes) -> bytes:
        """Compute O value for Revision 2"""
        # Similar to R3 but with 40-bit key
        padded_owner = self._pad_password_32(owner_pass)

        # MD5 hash
        hash_result = hashlib.md5(padded_owner).digest()

        # RC4 encryption with 40-bit key
        encrypted = self._rc4_encrypt(hash_result, key[:5])

        # Iterate 19 times
        for i in range(1, 20):
            new_key = bytes([b ^ i for b in key[:5]])
            encrypted = self._rc4_encrypt(encrypted, new_key)

        return encrypted

    def _compute_u_value_r4(self, user_pass: bytes, key: bytes) -> bytes:
        """Compute U value for Revision 4"""
        # Algorithm 4 for AES-128
        padded_user = self._pad_password_32(user_pass)

        # Generate random initialization vector
        iv = secrets.token_bytes(16)

        # Encrypt with AES-128
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=self._backend
        )
        encryptor = cipher.encryptor()

        # Pad and encrypt
        padded_data = self._pad_aes(padded_user)
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        return iv + encrypted

    def _compute_u_value_r3(self, user_pass: bytes, key: bytes) -> bytes:
        """Compute U value for Revision 3"""
        file_id = self.file_id
        if file_id is None:
            raise ValueError("file_id must be set before computing U value.")

        # Algorithm 4 for RC4-128
        self._pad_password_32(user_pass)

        # MD5 hash of padding string
        padding_hash = hashlib.md5(self.PADDING_STRING).digest()

        # Combine with file ID
        hash_input = padding_hash + file_id

        # Encrypt with RC4
        encrypted = self._rc4_encrypt(hash_input, key)

        # Pad to 32 bytes
        result = encrypted + bytes(16)  # 16 zero bytes

        return result[:32]

    def _compute_u_value_r2(self, user_pass: bytes, key: bytes) -> bytes:
        """Compute U value for Revision 2"""
        file_id = self.file_id
        if file_id is None:
            raise ValueError("file_id must be set before computing U value.")

        # Similar to R3 but with 40-bit key
        self._pad_password_32(user_pass)

        # MD5 hash of padding string
        padding_hash = hashlib.md5(self.PADDING_STRING).digest()

        # Combine with file ID
        hash_input = padding_hash + file_id

        # Encrypt with 40-bit RC4
        encrypted = self._rc4_encrypt(hash_input, key[:5])

        # Pad to 32 bytes
        result = encrypted + bytes(16)

        return result[:32]

    def _pad_password(self, password: bytes) -> bytes:
        """Pad password to 32 bytes (Algorithm 1)"""
        if len(password) >= 32:
            return password[:32]

        padded = password + self.PADDING_STRING[:32 - len(password)]
        return padded

    def _pad_password_32(self, password: bytes) -> bytes:
        """Pad password to exactly 32 bytes"""
        return self._pad_password(password)[:32]

    def _pad_aes(self, data: bytes) -> bytes:
        """Pad data for AES encryption (PKCS#7)"""
        padder = padding.PKCS7(128).padder()
        return padder.update(data) + padder.finalize()

    def _unpad_aes(self, data: bytes) -> bytes:
        """Unpad AES encrypted data"""
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(data) + unpadder.finalize()

    def encrypt_data(self, data: bytes, object_num: int, generation_num: int = 0) -> bytes:
        """Encrypt PDF object data"""
        if not self.encryption_key:
            raise ValueError("Encryption key has not been generated. Call generate_encryption_key first.")

        algorithm = self.options.algorithm

        # Generate object-specific key
        obj_key = self._generate_object_key(object_num, generation_num)

        if algorithm in [EncryptionAlgorithm.RC4_40, EncryptionAlgorithm.RC4_128]:
            # RC4 encryption
            encrypted_data = self._rc4_encrypt(data, obj_key)

        elif algorithm in [EncryptionAlgorithm.AES_128, EncryptionAlgorithm.AES_256]:
            # AES encryption
            encrypted_data = self._aes_encrypt(data, obj_key)

        else:
            raise ValueError(f"Invalid encryption algorithm: {algorithm}")

        return encrypted_data

    def decrypt_data(self, encrypted_data: bytes, object_num: int, generation_num: int = 0) -> bytes:
        """Decrypt PDF object data"""
        if not self.encryption_key:
            raise ValueError("Encryption key has not been generated.")

        algorithm = self.options.algorithm

        # Generate object-specific key
        obj_key = self._generate_object_key(object_num, generation_num)

        if algorithm in [EncryptionAlgorithm.RC4_40, EncryptionAlgorithm.RC4_128]:
            # RC4 decryption (RC4 is symmetric)
            decrypted_data = self._rc4_encrypt(encrypted_data, obj_key)

        elif algorithm in [EncryptionAlgorithm.AES_128, EncryptionAlgorithm.AES_256]:
            # AES decryption
            decrypted_data = self._aes_decrypt(encrypted_data, obj_key)

        else:
            raise ValueError(f"Invalid encryption algorithm: {algorithm}")

        return decrypted_data

    def _generate_object_key(self, object_num: int, generation_num: int) -> bytes:
        """Generate key for specific object"""
        encryption_key = self.encryption_key
        if encryption_key is None:
            raise ValueError("Encryption key has not been generated.")

        if self.options.revision >= 4:
            # For AES, the master key is used directly
            return encryption_key
        else:
            # For RC4, the key is combined with the object number
            key_input = encryption_key + struct.pack('<I', object_num)[:3] + struct.pack('<I', generation_num)[:2]

            if self.options.revision == 3:
                # Revision 3: MD5 hash
                return hashlib.md5(key_input).digest()[:min(16, len(encryption_key) + 5)]
            else:
                # Revision 2: 40-bit key
                return hashlib.md5(key_input).digest()[:5]

    def _rc4_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Optimized RC4 encryption implementation"""
        # Fast RC4 implementation with optimizations
        S = bytearray(256)
        for i in range(256):
            S[i] = i

        j = 0
        key_len = len(key)
        key_array = bytearray(key)

        # Key-scheduling algorithm (KSA)
        for i in range(256):
            j = (j + S[i] + key_array[i % key_len]) & 0xFF
            S[i], S[j] = S[j], S[i]

        # Pseudo-random generation algorithm (PRGA)
        i = j = 0
        result = bytearray(len(data))
        data_array = bytearray(data)

        for k in range(len(data)):
            i = (i + 1) & 0xFF
            j = (j + S[i]) & 0xFF
            S[i], S[j] = S[j], S[i]
            t = (S[i] + S[j]) & 0xFF
            result[k] = data_array[k] ^ S[t]

        return bytes(result)

    def _aes_encrypt(self, data: bytes, key: bytes) -> bytes:
        """AES encryption with CBC mode"""
        # Generate random IV
        iv = secrets.token_bytes(16)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(key[:32]),  # Use first 32 bytes for AES-256
            modes.CBC(iv),
            backend=self._backend
        )
        encryptor = cipher.encryptor()

        # Padding and encryption
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()

        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        # Combine IV with encrypted data
        return iv + encrypted

    def _aes_decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        """AES decryption with CBC mode"""
        if len(encrypted_data) < 32:  # IV (16) + at least one block (16)
            raise ValueError("Encrypted data is too short")

        # Extract IV
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]

        # Create cipher for decryption
        cipher = Cipher(
            algorithms.AES(key[:32]),
            modes.CBC(iv),
            backend=self._backend
        )
        decryptor = cipher.decryptor()

        # Decryption
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()

    def create_encryption_dictionary(self, file_id: bytes) -> dict[str, Any]:
        """Create PDF encryption dictionary according to standard"""
        if not self.encryption_key:
            self.generate_encryption_key(file_id)

        self.options.algorithm
        revision = self.options.revision

        # Create base encryption dictionary
        encrypt_dict = {
            'Filter': '/Standard',
            'V': self._get_encryption_version(),
            'R': revision,
            'Length': self.options.key_length,
            'P': struct.pack('<i', self.options.permissions).hex(),
            'EncryptMetadata': self.options.metadata_encrypted
        }

        # Add O and U values based on revision
        if revision >= 5:
            # PDF 2.0 (AES-256)
            encrypt_dict.update({
                'O': base64.b64encode(self._o_key).decode('ascii') if self._o_key else '',
                'U': base64.b64encode(self._u_key).decode('ascii') if self._u_key else '',
                'OE': base64.b64encode(self._oe_key).decode('ascii') if self._oe_key else '',
                'UE': base64.b64encode(self._ue_key).decode('ascii') if self._ue_key else '',
                'Perms': base64.b64encode(self._perms_key).decode('ascii') if self._perms_key else '',
            })

            # Crypt filters For PDF 2.0
            encrypt_dict['CF'] = {
                '/StdCF': {
                    'Type': '/CryptFilter',
                    'CFM': '/AESV3',
                    'AuthEvent': '/DocOpen',
                    'Length': 32  # 256-bit
                }
            }
            encrypt_dict['StmF'] = '/StdCF'
            encrypt_dict['StrF'] = '/StdCF'

        elif revision == 4:
            # PDF 1.7 ExtensionLevel 3 (AES-128)
            encrypt_dict.update({
                'O': self._o_key.hex() if self._o_key else '',
                'U': self._u_key.hex() if self._u_key else '',
                'Length': 128,
            })

            # Crypt filters
            encrypt_dict['CF'] = {
                '/StdCF': {
                    'Type': '/CryptFilter',
                    'CFM': '/AESV2',
                    'AuthEvent': '/DocOpen',
                    'Length': 16  # 128-bit
                }
            }
            encrypt_dict['StmF'] = '/StdCF'
            encrypt_dict['StrF'] = '/StdCF'

        elif revision == 3:
            # PDF 1.4 (RC4-128)
            encrypt_dict.update({
                'O': self._o_key.hex() if self._o_key else '',
                'U': self._u_key.hex() if self._u_key else '',
                'Length': 128,
            })

        elif revision == 2:
            # PDF 1.2 (RC4-40)
            encrypt_dict.update({
                'O': self._o_key.hex() if self._o_key else '',
                'U': self._u_key.hex() if self._u_key else '',
                'Length': 40,
            })

        # Add additional information for PDF 2.0
        if revision >= 5:
            encrypt_dict['SubFilter'] = '/adbe.pkcs7.s5'
            encrypt_dict['Recipients'] = []  # For public encryption

        self.encryption_dict = encrypt_dict
        return encrypt_dict

    def _get_encryption_version(self) -> int:
        """Determine encryption version based on algorithm"""
        if self.options.algorithm == EncryptionAlgorithm.AES_256:
            return 5  # PDF 2.0
        elif self.options.algorithm == EncryptionAlgorithm.AES_128:
            return 4  # PDF 1.7 ExtensionLevel 3
        elif self.options.algorithm == EncryptionAlgorithm.RC4_128:
            return 2  # PDF 1.4
        elif self.options.algorithm == EncryptionAlgorithm.RC4_40:
            return 1  # PDF 1.2
        else:
            return 2  # Default

    def validate_password(self, password: str, is_owner: bool = False) -> bool:
        """Password validation"""
        if not self.encryption_key or not self._u_key or not self._o_key:
            return False

        password_bytes = password.encode('utf-8')

        if is_owner:
            # Owner password validation
            if self.options.revision >= 5:
                # For PDF 2.0
                padded_password = self._pad_password_32(password_bytes)
                test_hash = hashlib.sha256(padded_password + self._o_key[:8]).digest()
                return hmac.compare_digest(test_hash[:32], self._o_key[:32])
            else:
                # For older versions
                padded_password = self._pad_password_32(password_bytes)
                test_key = self._compute_o_value_r3(padded_password, b'', self.encryption_key)
                return hmac.compare_digest(test_key, self._o_key)
        else:
            # User password validation
            if self.options.revision >= 5:
                padded_password = self._pad_password_32(password_bytes)
                test_hash = hashlib.sha256(padded_password + self._u_key[:8]).digest()
                return hmac.compare_digest(test_hash[:32], self._u_key[:32])
            else:
                padded_password = self._pad_password_32(password_bytes)
                test_key = self._compute_u_value_r3(padded_password, self.encryption_key)
                return hmac.compare_digest(test_key[:16], self._u_key[:16])

    def get_encryption_info(self) -> dict[str, Any]:
        """Get complete encryption info"""
        return {
            'algorithm': self.options.algorithm.value,
            'key_length': self.options.key_length,
            'revision': self.options.revision,
            'permissions': {
                'print': bool(self.options.permissions & PermissionFlag.PRINT),
                'modify': bool(self.options.permissions & PermissionFlag.MODIFY),
                'copy': bool(self.options.permissions & PermissionFlag.COPY),
                'annotate': bool(self.options.permissions & PermissionFlag.ANNOTATE),
                'form_fill': bool(self.options.permissions & PermissionFlag.FORM_FILL),
                'extract': bool(self.options.permissions & PermissionFlag.EXTRACT),
                'assemble': bool(self.options.permissions & PermissionFlag.ASSEMBLE),
                'print_high': bool(self.options.permissions & PermissionFlag.PRINT_HIGH),
                'modify_annotations': bool(self.options.permissions & PermissionFlag.MODIFY_ANNOTATIONS),
                'accessibility': bool(self.options.permissions & PermissionFlag.ACCESSIBILITY),
            },
            'metadata_encrypted': self.options.metadata_encrypted,
            'encrypt_attachments': self.options.encrypt_attachments,
            'encrypt_form_data': self.options.encrypt_form_data,
            'file_id': self.file_id.hex() if self.file_id else None,
            'encryption_key_length': len(self.encryption_key) * 8 if self.encryption_key else 0,
        }

    def get_permission_strings(self) -> list[str]:
        """Get list of permissions as strings"""
        permissions = []

        if self.options.permissions & PermissionFlag.PRINT:
            permissions.append("Print")
        if self.options.permissions & PermissionFlag.PRINT_HIGH:
            permissions.append("High quality print")
        if self.options.permissions & PermissionFlag.MODIFY:
            permissions.append("Modify content")
        if self.options.permissions & PermissionFlag.COPY:
            permissions.append("Copy")
        if self.options.permissions & PermissionFlag.ANNOTATE:
            permissions.append("Annotate")
        if self.options.permissions & PermissionFlag.FORM_FILL:
            permissions.append("Fill form")
        if self.options.permissions & PermissionFlag.EXTRACT:
            permissions.append("Extract")
        if self.options.permissions & PermissionFlag.ASSEMBLE:
            permissions.append("Assemble")
        if self.options.permissions & PermissionFlag.MODIFY_ANNOTATIONS:
            permissions.append("Modify annotations")
        if self.options.permissions & PermissionFlag.ACCESSIBILITY:
            permissions.append("Accessibility")

        return permissions


class PDFSecurityHandler:
    """PDF security and encryption management"""

    @staticmethod
    def create_encryptor(options: EncryptionOptions) -> PDFEncryptor:
        """Create PDF encryptor"""
        return PDFEncryptor(options)

    @staticmethod
    def generate_file_id() -> bytes:
        """Generate unique file identifier"""
        # Combine timestamp and random bytes
        timestamp = struct.pack('<Q', int(time.time() * 1000))
        random_bytes = secrets.token_bytes(16)
        return hashlib.md5(timestamp + random_bytes).digest()

    @staticmethod
    def check_password_strength(password: str) -> dict[str, Any]:
        """Check password strength"""
        score = 0
        feedback = []

        # Check length
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            feedback.append("Password is too short (minimum 8 characters)")

        # Check character variety
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if has_upper:
            score += 1
        else:
            feedback.append("Add uppercase letters")

        if has_lower:
            score += 1
        else:
            feedback.append("Add lowercase letters")

        if has_digit:
            score += 1
        else:
            feedback.append("Add digits")

        if has_special:
            score += 1
        else:
            feedback.append("Add special characters")

        # Final assessment
        if score >= 6:
            strength = "Strong"
        elif score >= 4:
            strength = "Medium"
        else:
            strength = "Weak"

        return {
            'score': score,
            'strength': strength,
            'feedback': feedback,
            'length': len(password),
            'has_upper': has_upper,
            'has_lower': has_lower,
            'has_digit': has_digit,
            'has_special': has_special
        }

    @staticmethod
    def get_supported_algorithms() -> list[dict[str, Any]]:
        """Get list of supported algorithms"""
        return [
            {
                'algorithm': 'AES_256',
                'name': 'AES-256',
                'description': 'Standard advanced encryption 256-bit (PDF 2.0)',
                'key_length': 256,
                'revision': 5,
                'security_level': 'Very high'
            },
            {
                'algorithm': 'AES_128',
                'name': 'AES-128',
                'description': 'Standard advanced encryption 128-bit (PDF 1.7)',
                'key_length': 128,
                'revision': 4,
                'security_level': 'High'
            },
            {
                'algorithm': 'RC4_128',
                'name': 'RC4-128',
                'description': 'RC4 128-bit encryption (PDF 1.4)',
                'key_length': 128,
                'revision': 3,
                'security_level': 'Medium'
            },
            {
                'algorithm': 'RC4_40',
                'name': 'RC4-40',
                'description': 'RC4 40-bit encryption (PDF 1.2)',
                'key_length': 40,
                'revision': 2,
                'security_level': 'Low'
            }
        ]
