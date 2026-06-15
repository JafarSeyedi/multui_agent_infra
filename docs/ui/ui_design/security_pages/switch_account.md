## ✅ صفحه سوئیچ کاربر / حساب (Switch User / Account)

این صفحه به کاربر اجازه می‌دهد:

- بین **حساب‌های** کاربر فعلی جابجا شود (**بدون نیاز به تأیید مجدد**).
- بین **کاربران دیگر** (افراد حقیقی) که در این دستگاه قبلاً وارد شده‌اند جابجا شود (**نیاز به تأیید OTP**).
- **کاربر جدید** اضافه کند (ثبت‌نام کاربر جدید با کد ملی، شماره موبایل و OTP؛ با بررسی یکتایی کد ملی).
- **حساب جدید** برای کاربر فعلی یا هر کاربر دیگر ایجاد کند (درخواست ایجاد حساب با نقش اصلی جدید).
- **حساب پیش‌فرض** هر کاربر را با آیکون ستاره توپر/توخالی تغییر دهد.

**نکات کلیدی:**
- کد ملی هرگز در رابط کاربری نمایش داده نمی‌شود.
- برای کاربر فعلی، دکمه «تغییر به این کاربر» نمایش داده نمی‌شود (فقط عبارت «(فعلی)» در کنار نام کاربر).
- برای جابجایی بین حساب‌های کاربر فعلی، از دکمه «انتخاب» استفاده می‌شود.
- ثبت‌نام کاربر جدید و ایجاد حساب جدید در بک‌اند یکتایی کد ملی را بررسی می‌کنند (در صفحات مربوطه پیاده‌سازی شده است).
- تمام اطلاعات کاربران و حساب‌های آن‌ها در دستگاه به صورت محلی (SecureStore) ذخیره می‌شود و هر بار پس از هر ورود یا تغییر کاربر، با سرور همگام می‌گردد.

---

## ۱. رابط کاربری (UI) صفحه به صورت مودال

```
┌─────────────────────────────────────────────────────────────┐
│                    انتخاب کاربر / حساب                      │
├─────────────────────────────────────────────────────────────┤
│ 👤 علی رضایی (فعلی)                                        │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ معلم                                        ⭐   انتخاب │ │
│   │ نقش‌ها: معلم ریاضی هشتم، معلم ریاضی هفتم               │ │
│   ├───────────────────────────────────────────────────────┤ │
│   │ والدین                                      ☆   انتخاب │ │
│   │ نقش‌ها: والدین سارا رضایی                             │ │
│   └───────────────────────────────────────────────────────┘ │
│   [+ افزودن حساب جدید برای علی]                            │
├─────────────────────────────────────────────────────────────┤
│ 👤 سارا رضایی                                               │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ دانش‌آموز                                   ☆   انتخاب │ │
│   │ نقش‌ها: عضو کلاس دوم ابتدایی                          │ │
│   └───────────────────────────────────────────────────────┘ │
│   [تغییر به این کاربر]  (+ افزودن حساب جدید برای سارا)     │
├─────────────────────────────────────────────────────────────┤
│ + افزودن کاربر جدید                                        │
├─────────────────────────────────────────────────────────────┤
│                         [بستن]                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ۲. کامپوننت‌ها (UI Components)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `ModalContainer` | مودال | صفحه به صورت مودال تمام‌صفحه (یا نیمه‌صفحه) با قابلیت بستن |
| `Title` | متن | «انتخاب کاربر / حساب» |
| `UserSection` | View (کارت) | نمایش اطلاعات یک کاربر (نام، وضعیت فعلی، لیست حساب‌ها، دکمه‌ها) |
| `UserNameRow` | View | شامل نام کاربر + نشان «(فعلی)» (در صورت جاری بودن) + دکمه «تغییر به این کاربر» (در صورت نبودن جاری) |
| `AccountList` | FlatList | لیست حساب‌های آن کاربر |
| `AccountItem` | View | هر ردیف حساب: نوع اکانت (نقش اصلی)، خلاصه نقش‌های تابعه، آیکون ستاره (⭐/☆)، دکمه «انتخاب» |
| `StarIcon` | TouchableOpacity | آیکون ستاره توپر (پیش‌فرض) / توخالی (غیر پیش‌فرض) – با کلیک، درخواست تغییر پیش‌فرض |
| `SelectAccountButton` | TouchableOpacity | دکمه «انتخاب» برای جابجایی به آن حساب (در همان کاربر فعلی) |
| `SwitchUserButton` | TouchableOpacity | دکمه «تغییر به این کاربر» (برای کاربران غیرجاری) – باز کردن مودال OTP |
| `AddAccountButton` | TouchableOpacity | «+ افزودن حساب جدید برای [نام کاربر]» – هدایت به صفحه ایجاد حساب جدید |
| `AddNewUserButton` | TouchableOpacity | «+ افزودن کاربر جدید» – هدایت به صفحه ثبت‌نام کاربر جدید |
| `CloseButton` | TouchableOpacity | بستن مودال |

---

## ۳. منطق فرانت‌اند (React Native + Expo)

### ۳.۱. ذخیره‌سازی محلی (SecureStore)

ساختار داده ذخیره شده در دستگاه:

```json
{
  "users": [
    {
      "nationalId": "1234567890",
      "fullName": "علی رضایی",
      "phone": "+989123456789",
      "accounts": [
        {
          "accountId": "acc_1",
          "accountType": "معلم",
          "isDefault": true,
          "secondaryRoles": ["معلم ریاضی هشتم", "معلم ریاضی هفتم"]
        },
        {
          "accountId": "acc_2",
          "accountType": "والدین",
          "isDefault": false,
          "secondaryRoles": ["والدین سارا رضایی"]
        }
      ]
    },
    {
      "nationalId": "0987654321",
      "fullName": "سارا رضایی",
      "phone": "+989123456780",
      "accounts": [
        {
          "accountId": "acc_3",
          "accountType": "دانش‌آموز",
          "isDefault": true,
          "secondaryRoles": ["عضو کلاس دوم ابتدایی"]
        }
      ]
    }
  ],
  "currentUserId": "1234567890",
  "currentAccountId": "acc_1"
}
```

**توابع کمکی:**
- `getLocalUsers()`: خواندن داده از SecureStore.
- `saveLocalUsers(data)`: نوشتن داده در SecureStore.
- `setCurrentUserAndAccount(userId, accountId)`: به‌روزرسانی `currentUserId` و `currentAccountId`.

### ۳.۲. کامپوننت اصلی

```tsx
// components/UserAccountSwitcherModal.tsx
import React, { useState, useEffect } from 'react';
import { Modal, View, Text, TouchableOpacity, FlatList, Alert, ActivityIndicator } from 'react-native';
import { api } from '../services/api';
import { storeToken } from '../utils/storage';
import { getLocalUsers, saveLocalUsers, setCurrentUserAndAccount } from '../utils/localUserStorage';
import { useNavigation, CommonActions } from '@react-navigation/native';

export default function UserAccountSwitcherModal({ visible, onClose }) {
  const [users, setUsers] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [currentAccountId, setCurrentAccountId] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigation = useNavigation();

  useEffect(() => {
    if (visible) loadLocalData();
  }, [visible]);

  const loadLocalData = async () => {
    const data = await getLocalUsers();
    setUsers(data.users || []);
    setCurrentUserId(data.currentUserId);
    setCurrentAccountId(data.currentAccountId);
    setLoading(false);
  };

  const refreshLocalData = async () => {
    setLoading(true);
    await loadLocalData();
    setLoading(false);
  };

  const syncLocalUserData = async (userId, freshAccounts) => {
    const local = await getLocalUsers();
    const userIndex = local.users.findIndex(u => u.nationalId === userId);
    if (userIndex !== -1) {
      local.users[userIndex].accounts = freshAccounts;
    }
    await saveLocalUsers(local);
    await refreshLocalData();
  };

  // جابجایی بین حساب‌های همان کاربر (بدون OTP)
  const switchAccount = async (userId, accountId) => {
    if (userId !== currentUserId) {
      Alert.alert('توجه', 'لطفاً ابتدا کاربر را تغییر دهید.');
      return;
    }
    try {
      const res = await api.post('/auth/switch-account', { accountId });
      await storeToken(res.data.token);
      await setCurrentUserAndAccount(userId, accountId);
      onClose();
      navigation.dispatch(CommonActions.reset({ index: 0, routes: [{ name: 'MainApp' }] }));
    } catch (err) {
      Alert.alert('خطا', 'تغییر حساب انجام نشد');
    }
  };

  // نمایش مودال OTP برای تغییر کاربر
  const promptOtpForUser = (targetUserId, targetAccountId) => {
    const targetUser = users.find(u => u.nationalId === targetUserId);
    if (!targetUser) return;
    Alert.prompt(
      'تأیید هویت',
      `کد تأیید به شماره ${targetUser.phone} ارسال شد. کد ۶ رقمی را وارد کنید.`,
      [
        { text: 'لغو', style: 'cancel' },
        {
          text: 'تأیید',
          onPress: async (otp) => {
            try {
              const res = await api.post('/auth/switch-user-verify', { nationalId: targetUserId, otp });
              const { token, accounts, defaultAccountId } = res.data;
              await storeToken(token);
              await syncLocalUserData(targetUserId, accounts);
              await setCurrentUserAndAccount(targetUserId, defaultAccountId);
              onClose();
              navigation.dispatch(CommonActions.reset({ index: 0, routes: [{ name: 'MainApp' }] }));
            } catch (err) {
              Alert.alert('خطا', 'کد تأیید اشتباه است');
            }
          },
        },
      ],
      'plain-text'
    );
  };

  const switchUser = async (targetUserId, targetAccountId) => {
    // درخواست OTP به سرور
    try {
      await api.post('/auth/switch-user-request-otp', { nationalId: targetUserId });
      promptOtpForUser(targetUserId, targetAccountId);
    } catch (err) {
      Alert.alert('خطا', 'ارسال کد ممکن نیست');
    }
  };

  const setDefaultAccount = async (userId, accountId) => {
    if (userId !== currentUserId) {
      Alert.alert('توجه', 'برای تغییر حساب پیش‌فرض یک کاربر دیگر، ابتدا به آن کاربر سوئیچ کنید.');
      return;
    }
    try {
      await api.put(`/user/accounts/${accountId}/set-default`);
      await refreshLocalData();
      Alert.alert('انجام شد', 'حساب پیش‌فرض تغییر کرد.');
    } catch (err) {
      Alert.alert('خطا', 'تنظیم پیش‌فرض انجام نشد');
    }
  };

  const addAccountForUser = (userId) => {
    onClose();
    navigation.navigate('CreateAccount', { forUserId: userId });
  };

  const addNewUser = () => {
    onClose();
    navigation.navigate('RegisterNewUser');
  };

  const renderAccountItem = ({ item: account, userId }) => {
    const isCurrent = (userId === currentUserId && account.accountId === currentAccountId);
    return (
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 12, borderBottomWidth: 0.5, borderColor: '#eee' }}>
        <View style={{ flex: 1 }}>
          <Text style={{ fontWeight: 'bold', fontSize: 16 }}>{account.accountType}</Text>
          {account.secondaryRoles && account.secondaryRoles.length > 0 && (
            <Text style={{ fontSize: 12, color: '#666', marginTop: 2 }}>نقش‌ها: {account.secondaryRoles.join('، ')}</Text>
          )}
        </View>
        <TouchableOpacity onPress={() => setDefaultAccount(userId, account.accountId)} style={{ marginHorizontal: 12 }}>
          <Text style={{ fontSize: 26, color: '#f5a623' }}>{account.isDefault ? '⭐' : '☆'}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => switchAccount(userId, account.accountId)}>
          <Text style={{ color: '#0066cc', fontWeight: 'bold', fontSize: 14 }}>انتخاب</Text>
        </TouchableOpacity>
      </View>
    );
  };

  const renderUserSection = ({ item: user }) => {
    const isCurrentUser = (user.nationalId === currentUserId);
    return (
      <View style={{ marginBottom: 24, backgroundColor: isCurrentUser ? '#e6f7ff' : '#fff', borderRadius: 16, padding: 16, elevation: 2 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold' }}>{user.fullName}</Text>
          {isCurrentUser ? (
            <Text style={{ fontSize: 12, color: '#0066cc', fontWeight: 'bold' }}>(فعلی)</Text>
          ) : (
            <TouchableOpacity onPress={() => switchUser(user.nationalId, user.accounts[0]?.accountId)} style={{ backgroundColor: '#4caf50', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 }}>
              <Text style={{ color: '#fff', fontSize: 12 }}>تغییر به این کاربر</Text>
            </TouchableOpacity>
          )}
        </View>
        <FlatList
          data={user.accounts}
          keyExtractor={(acc) => acc.accountId}
          renderItem={(props) => renderAccountItem({ ...props, userId: user.nationalId })}
          scrollEnabled={false}
        />
        <TouchableOpacity onPress={() => addAccountForUser(user.nationalId)} style={{ marginTop: 12, alignSelf: 'flex-start' }}>
          <Text style={{ color: '#0066cc', fontSize: 12 }}>+ افزودن حساب جدید برای {user.fullName}</Text>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false} onRequestClose={onClose}>
      <View style={{ flex: 1, padding: 20, paddingTop: 40, backgroundColor: '#f5f5f5' }}>
        <Text style={{ fontSize: 28, textAlign: 'center', marginBottom: 24 }}>انتخاب کاربر / حساب</Text>
        {loading ? (
          <ActivityIndicator size="large" color="#0066cc" />
        ) : (
          <FlatList
            data={users}
            keyExtractor={(user) => user.nationalId}
            renderItem={renderUserSection}
            contentContainerStyle={{ paddingBottom: 20 }}
            ListEmptyComponent={<Text style={{ textAlign: 'center', marginTop: 50 }}>هیچ کاربری یافت نشد. لطفاً اولین کاربر را اضافه کنید.</Text>}
          />
        )}
        <TouchableOpacity onPress={addNewUser} style={{ paddingVertical: 14, alignItems: 'center', borderTopWidth: 1, borderColor: '#ccc', marginTop: 10 }}>
          <Text style={{ color: '#0066cc', fontSize: 16 }}>+ افزودن کاربر جدید</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onClose} style={{ marginTop: 20, alignItems: 'center', padding: 12 }}>
          <Text style={{ fontSize: 16, color: '#888' }}>بستن</Text>
        </TouchableOpacity>
      </View>
    </Modal>
  );
}
```

### ۳.۳. ویجت ثابت (Account Switcher Widget)

این ویجت در نوار بالایی یا پایینی همه صفحات اصلی قرار می‌گیرد.

```tsx
// components/UserAccountSwitcherWidget.tsx
import React, { useState } from 'react';
import { TouchableOpacity, Text } from 'react-native';
import UserAccountSwitcherModal from './UserAccountSwitcherModal';
import { useCurrentAccountStore } from '../stores/currentAccountStore';

export default function UserAccountSwitcherWidget() {
  const [modalVisible, setModalVisible] = useState(false);
  const currentDisplayName = useCurrentAccountStore((state) => state.currentDisplayName);
  return (
    <>
      <TouchableOpacity onPress={() => setModalVisible(true)} style={{ paddingHorizontal: 12, paddingVertical: 8, flexDirection: 'row', alignItems: 'center' }}>
        <Text style={{ fontSize: 14, color: '#333' }}>{currentDisplayName || 'حساب من'} ▼</Text>
      </TouchableOpacity>
      <UserAccountSwitcherModal visible={modalVisible} onClose={() => setModalVisible(false)} />
    </>
  );
}
```

---

## ۴. منطق بک‌اند (FastAPI + PostgreSQL + Redis)

### ۴.۱. مدل داده (مرور)

```sql
-- کاربران (اشخاص حقیقی)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    national_id VARCHAR(10) UNIQUE NOT NULL,
    phone VARCHAR(13) UNIQUE NOT NULL,
    phone_verified_at TIMESTAMP,
    national_id_verified_at TIMESTAMP,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT now()
);

-- اکانت‌ها (هر کاربر چند اکانت)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_type VARCHAR(50) NOT NULL, -- 'student', 'teacher', 'parent', ...
    display_name VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);

-- نقش‌های تابعه
CREATE TABLE account_secondary_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    role_type VARCHAR(50) NOT NULL,
    context_id UUID, -- e.g., class_id, course_id, school_id
    context_name VARCHAR(255), -- برای نمایش سریع در UI
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT now()
);
```

### ۴.۲. APIهای مورد نیاز

#### (1) `POST /auth/switch-user-request-otp`
- **بدن:** `{ nationalId }`
- **بررسی:** کاربر با این nationalId وجود دارد.
- **عملیات:** تولید OTP ۶ رقمی، ذخیره در Redis با کلید `otp:switch_user:{nationalId}` (انقضا ۵ دقیقه)، ارسال OTP به شماره موبایل کاربر.
- **نرخ محدودیت:** هر nationalId حداکثر ۳ بار در ساعت، هر IP حداکثر ۱۰ بار در ساعت.
- **پاسخ:** `{ message: "کد ارسال شد" }`

#### (2) `POST /auth/switch-user-verify`
- **بدن:** `{ nationalId, otp }`
- **بررسی OTP** از Redis.
- **عملیات:** در صورت صحت، JWT جدید صادر می‌شود (سطح ۱) با payload شامل `userId`, `level=1`. همچنین لیست اکانت‌های کاربر به همراه نقش‌های تابعه (با نام‌های قابل نمایش) و `defaultAccountId` بازگردانده می‌شود.
- **پاسخ:** `{ token, accounts: [ { accountId, accountType, isDefault, secondaryRoles: [ "نام نقش1", "نام نقش2" ] } ], defaultAccountId }`

#### (3) `POST /auth/switch-account`
- **بدن:** `{ accountId }`
- **بررسی:** accountId متعلق به همان userId است (از توکن فعلی).
- **عملیات:** تولید JWT جدید با payload شامل `userId`, `accountId`, `accountType`, `level=1`.
- **پاسخ:** `{ token }`

#### (4) `PUT /user/accounts/{accountId}/set-default`
- **نیاز به توکن سطح ۱.**
- **بررسی:** accountId متعلق به userId توکن است.
- **عملیات:** در جدول `accounts`، `is_default` این اکانت = true و سایر اکانت‌های همان کاربر = false.
- **پاسخ:** `{ message: "default account updated" }`

---

## ۵. ملاحظات امنیتی و کامل بودن فرایندها

| نیاز | نحوه تأمین |
|------|-------------|
| **عدم نمایش کد ملی** | در هیچ جای UI کد ملی نمایش داده نمی‌شود (فقط در درخواست‌های API استفاده می‌شود). |
| **یکتایی کد ملی در ثبت‌نام** | در API ثبت‌نام (`/auth/signup/verify`) و ایجاد کاربر جدید، یکتایی بررسی می‌شود (constraint دیتابیس). |
| **جلوگیری از سوئیچ کاربر بدون OTP** | تغییر کاربر نیاز به OTP دارد (API `switch-user-verify`). |
| **جلوگیری از تغییر حساب دیگران** | تمام APIها مالکیت را بر اساس توکن بررسی می‌کنند. |
| **ذخیره امن اطلاعات محلی** | از SecureStore (Expo) استفاده می‌شود. رمزگذاری شده است. |
| **عدم قابلیت جعل درخواست** | تمام درخواست‌ها با توکن JWT امضا شده و اعتبارسنجی می‌شوند. |

---

## ۶. نحوه همگام‌سازی کش محلی با سرور

- هر بار که کاربر لاگین می‌کند (صفحه ورود/ثبت‌نام)، اطلاعات کامل کاربر و اکانت‌هایش از سرور دریافت و در کش محلی ذخیره می‌شود.
- پس از هر تغییر کاربر (با OTP)، اطلاعات جدید از سرور دریافت و کش به‌روز می‌شود.
- پس از تغییر حساب پیش‌فرض، کش محلی به‌روز می‌شود (با فراخوانی `refreshLocalData`).
- پس از ایجاد حساب جدید یا افزودن کاربر جدید، کش محلی باید به‌روز شود (در صفحه CreateAccount و RegisterNewUser پس از موفقیت، فراخوانی `syncLocalUserData` انجام شود).

---

## ۷. جمع‌بندی

این صفحه تمام عملکردهای درخواستی را پوشش می‌دهد:
- نمایش کاربران و حساب‌های آن‌ها.
- جابجایی بین حساب‌های کاربر فعلی (بدون OTP).
- جابجایی بین کاربران دیگر (با OTP).
- افزودن کاربر جدید (ثبت‌نام) و افزودن حساب جدید (ایجاد اکانت).
- تغییر حساب پیش‌فرض با آیکون ستاره.
- عدم نمایش کد ملی و رعایت امنیت.

