## ✅ صفحه ورود / ثبت‌نام یکپارچه – هوشیاد

### ۱. هدف صفحه
کاربر با وارد کردن **کد ملی (۱۰ رقم)** و **شماره موبایل (با پیش‌شماره +98)** وارد سامانه می‌شود. سامانه در پشت‌صحنه تشخیص می‌دهد که کاربر قبلاً ثبت‌نام کرده است یا خیر. در هر دو حالت، یک کد تأیید ۶ رقمی (OTP) به شماره موبایل ارسال می‌شود. پس از تأیید OTP، اگر کاربر جدید باشد، فقط یک رکورد کاربر در دیتابیس ایجاد می‌شود (بدون هیچ اکانتی) و به صفحه درخواست نقش اولیه هدایت می‌گردد. اگر کاربر قدیمی باشد، لیست اکانت‌های خود را دریافت کرده و بسته به تعداد اکانت‌ها، یا مستقیماً وارد داشبورد می‌شود یا به صفحه انتخاب اکانت می‌رود.

**هیچ اشاره‌ای به نقش یا کلاس در این صفحه وجود ندارد.**  
**هیچ رمز عبوری استفاده نمی‌شود.**  

---

### ۲. اجزای صفحه (کامپوننت‌ها)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `LogoTitle` | متن | نام «هوشیاد» در بالای صفحه (بدون عنوان «هدر») |
| `NationalIdInput` | فیلد ورودی | کد ملی ۱۰ رقم، فقط عدد، اعتبارسنجی سمت کلاینت با الگوریتم کنترل |
| `PhonePrefixSelect` | کامبوی تک انتخابی | گزینه‌های پیش‌شماره (فعلاً فقط 🇮🇷 +98) |
| `PhoneNumberInput` | فیلد ورودی | شماره موبایل ۱۰ رقم (بدون صفر اول)، مثال: ۹۱۲۳۴۵۶۷۸۹ |
| `RequestOtpButton` | دکمه | ارسال درخواست OTP – پس از کلیک و موفقیت، به مدت ۱۲۰ ثانیه غیرفعال می‌شود |
| `OtpInput` | فیلد ورودی | کد ۶ رقمی، پشتیبانی از Paste خودکار |
| `VerifyButton` | دکمه | تأیید نهایی و ورود/ثبت‌نام |
| `WarningText` | متن | هشدار حقوقی در پایین صفحه: «وارد کردن اطلاعات نادرست و استفاده از هویت دیگران پیگرد قانونی دارد.» |
| `ErrorMessage` | متن | نمایش خطاهای اعتبارسنجی یا سرور (مغایرت شماره، کد ملی تکراری، OTP اشتباه، نرخ محدودیت) |

---

### ۳. منطق فرانت‌اند (React Native + Expo)

```tsx
// utils/validation.ts
export const validateNationalId = (id: string): boolean => {
  if (!/^\d{10}$/.test(id)) return false;
  // الگوریتم کنترل کد ملی (mod 11)
  let sum = 0;
  for (let i = 0; i < 9; i++) sum += parseInt(id[i]) * (10 - i);
  const remainder = sum % 11;
  const control = parseInt(id[9]);
  return (remainder < 2 && control === remainder) || (remainder >= 2 && control === 11 - remainder);
};

export const validatePhone = (phone: string): boolean => /^\d{10}$/.test(phone);
```

```tsx
// screens/UnifiedLogin.tsx
import { useState } from 'react';
import { View, Text, TextInput, Button, TouchableOpacity } from 'react-native';
import { api } from '../services/api';
import { storeToken } from '../utils/storage';

export default function UnifiedLoginScreen({ navigation }) {
  const [nationalId, setNationalId] = useState('');
  const [phonePrefix, setPhonePrefix] = useState('+98');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [isOtpSent, setIsOtpSent] = useState(false);
  const [timer, setTimer] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const startCountdown = () => {
    const interval = setInterval(() => {
      setTimer((prev) => {
        if (prev <= 1) { clearInterval(interval); return 0; }
        return prev - 1;
      });
    }, 1000);
  };

  const requestOtp = async () => {
    if (!validateNationalId(nationalId)) { setError('کد ملی ۱۰ رقمی معتبر نیست'); return; }
    if (!validatePhone(phoneNumber)) { setError('شماره موبایل ۱۰ رقمی معتبر نیست'); return; }
    setIsLoading(true);
    try {
      await api.post('/auth/request-otp', { nationalId, phone: `${phonePrefix}${phoneNumber}` });
      setIsOtpSent(true);
      setTimer(120);
      startCountdown();
      setError('');
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError('کد ملی با شماره موبایل دیگری ثبت شده است. در صورت اشتباه، با پشتیبانی تماس بگیرید.');
      } else if (err.response?.status === 429) {
        setError('درخواست بیش از حد مجاز. چند دقیقه دیگر تلاش کنید.');
      } else {
        setError('خطا در ارسال پیامک. بعداً تلاش کنید.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const verify = async () => {
    if (otp.length !== 6) { setError('کد ۶ رقمی را وارد کنید'); return; }
    setIsLoading(true);
    try {
      const res = await api.post('/auth/verify', { nationalId, phone: `${phonePrefix}${phoneNumber}`, otp });
      const { token, isNewUser, accounts, defaultAccountId, hasMultipleAccounts } = res.data;
      await storeToken(token);
      if (isNewUser) {
        navigation.replace('RoleRequest'); // صفحه درخواست نقش اولیه
      } else {
        if (hasMultipleAccounts) {
          navigation.replace('AccountSelector', { accounts, defaultAccountId });
        } else if (accounts.length === 1) {
          navigateToDashboard(accounts[0]); // تابعی که بر اساس نقش به صفحه اصلی مناسب هدایت می‌کند
        } else {
          navigation.replace('RoleRequest'); // حالت غیرمنتظره
        }
      }
    } catch (err: any) {
      setError('کد تأیید اشتباه است یا منقضی شده');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 32, textAlign: 'center', marginBottom: 40 }}>هوشیاد</Text>

      <TextInput placeholder="کد ملی (۱۰ رقم)" value={nationalId} onChangeText={setNationalId} keyboardType="number-pad" maxLength={10} />
      <View style={{ flexDirection: 'row', marginTop: 16 }}>
        <View style={{ flex: 1 }}><TextInput value={phonePrefix} editable={false} /></View>
        <TextInput placeholder="۹۱۲۳۴۵۶۷۸۹" value={phoneNumber} onChangeText={setPhoneNumber} keyboardType="number-pad" maxLength={10} style={{ flex: 3 }} />
      </View>

      <Button title="ارسال کد تأیید" onPress={requestOtp} disabled={isLoading || timer > 0} />
      {timer > 0 && <Text>ارسال مجدد کد پس از {timer} ثانیه</Text>}

      {isOtpSent && (
        <>
          <TextInput placeholder="کد ۶ رقمی" value={otp} onChangeText={setOtp} keyboardType="number-pad" maxLength={6} style={{ marginTop: 16 }} />
          <Button title="ورود / ثبت‌نام" onPress={verify} disabled={isLoading} />
        </>
      )}

      {error ? <Text style={{ color: 'red', marginTop: 16 }}>{error}</Text> : null}
      <Text style={{ fontSize: 12, color: '#888', marginTop: 40, textAlign: 'center' }}>
        ⚠️ وارد کردن اطلاعات نادرست و استفاده از هویت دیگران پیگرد قانونی دارد.
      </Text>
    </View>
  );
}
```

---

### ۴. منطق بک‌اند (FastAPI + PostgreSQL + Redis)

#### مدل داده (اولیه)

```sql
-- جدول کاربران (هیچ اکانتی در این مرحله ساخته نمی‌شود)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    national_id VARCHAR(10) UNIQUE NOT NULL,
    phone VARCHAR(13) UNIQUE NOT NULL,      -- با پیش‌شماره مثل +989123456789
    phone_verified_at TIMESTAMP,
    national_id_verified_at TIMESTAMP,      -- برای سطح 2 (تأیید کد ملی)
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_users_national_id ON users(national_id);
CREATE INDEX idx_users_phone ON users(phone);
```

#### API: `POST /auth/request-otp`

**بدن درخواست:** `{ nationalId: string, phone: string }` (phone شامل پیش‌شماره)

**مراحل پردازش:**
1. اعتبارسنجی کد ملی (۱۰ رقم، الگوریتم کنترل) و شماره موبایل (باید با regex `^\+\d{11,13}$` مطابقت داشته باشد – فعلاً +98).
2. دریافت IP و user-agent از هدر.
3. **نرخ‌محدودیت:**
   - هر nationalId: حداکثر ۳ درخواست در ساعت (کلید Redis `ratelimit:otp_req:national:{nationalId}`).
   - هر IP: حداکثر ۱۰ درخواست در ساعت (`ratelimit:otp_req:ip:{ip}`).
4. بروز خطا در صورت تجاوز از نرخ.
5. **بررسی مغایرت:** جستجوی کاربر با `national_id`. اگر یافت شد و `phone` آن کاربر با شماره درخواست متفاوت بود → پاسخ `409 Conflict` با پیام «کد ملی با شماره موبایل دیگری ثبت شده است».
6. اگر کاربر یافت نشد (کاربر جدید): ذخیره یک رکورد موقت در Redis با کلید `pending_user:{nationalId}` شامل `phone` و `ttl=600` ثانیه.
7. **تولید OTP** ۶ رقمی تصادفی، ذخیره در Redis با کلید `otp:{nationalId}` و `ttl=300` ثانیه.
8. ارسال OTP از طریق سرویس پیامک (با در نظر گرفتن محدودیت ارسال برای هر شماره، مثلاً ۳ بار در ساعت).
9. ثبت لاگ درخواست (جدول `request_logs` با `ip`, `user_agent`, `national_id`).
10. پاسخ: `{ message: "کد ارسال شد", expiresIn: 300 }`

#### API: `POST /auth/verify`

**بدن درخواست:** `{ nationalId: string, phone: string, otp: string }`

**مراحل پردازش:**
1. اعتبارسنجی ورودی‌ها.
2. بازیابی OTP از Redis با کلید `otp:{nationalId}`. اگر وجود نداشت یا مطابقت نداشت:
   - افزایش شمارش تلاش ناموفق برای nationalId (Redis `failed_otp_attempts:{nationalId}`). پس از ۵ بار، قفل ۳۰ دقیقه‌ای (`otp_lock:{nationalId}`).
   - پاسخ `401 Unauthorized`.
3. اگر OTP درست بود:
   - **حالت ۱: کاربر وجود دارد** (جستجو در جدول `users` با `national_id`).
     - به‌روزرسانی `phone_verified_at = now()` (اگر قبلاً تأیید نشده بود).
     - دریافت لیست اکانت‌ها (از جدول `accounts` – که فعلاً خالی است، بعداً پرشده).
     - تولید JWT (سطح ۱) با payload:
       ```json
       { "userId": "...", "level": 1, "exp": now+30days }
       ```
     - پاسخ:
       ```json
       {
         "token": "...",
         "isNewUser": false,
         "accounts": [...],
         "defaultAccountId": "uuid or null",
         "hasMultipleAccounts": boolean
       }
       ```
   - **حالت ۲: کاربر جدید** (nationalId در دیتابیس وجود ندارد):
     - بازیابی اطلاعات موقت از `pending_user:{nationalId}`. اگر وجود نداشت → خطا (احتمالاً timeout).
     - ایجاد رکورد جدید در `users` با:
       - `national_id`, `phone`, `phone_verified_at = now()`, `national_id_verified_at = NULL`
       - `id` جدید
     - حذف کلید `pending_user:{nationalId}`.
     - تولید JWT (سطح ۱) با `userId`.
     - پاسخ:
       ```json
       {
         "token": "...",
         "isNewUser": true,
         "accounts": []
       }
       ```
4. حذف کلید OTP از Redis.
5. پاسخ موفق.

**جدول `accounts` (برای کاربران قدیمی) – فعلاً تعریف می‌شود اما محتوایی ندارد:**

```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    primary_role VARCHAR(50) NOT NULL,
    display_name VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);
```

---

### ۵. ملاحظات امنیتی

| تهدید | راهکار |
|--------|--------|
| **DDoS روی endpoint های لاگین** | نرخ‌محدودیت (IP و nationalId)، استفاده از Cloudflare یا API Gateway |
| **تخمین OTP** | کد ۶ رقمی، محدودیت ۵ تلاش، قفل موقت پس از ۵ بار |
| **بمباران پیامکی** | محدودیت ۳ درخواست OTP در ساعت به ازای هر nationalId |
| **تطابق شماره با کد ملی** | بررسی مغایرت در بک‌اند (409 Conflict) |
| **ذخیره توکن** | JWT با امضای HS256 یا RS256، ذخیره در SecureStore (موبایل) یا HttpOnly Cookie (وب) |
| **ورود همزمان از چند دستگاه** | مجاز است (هر نشست مستقل). مدیریت نشست‌ها در صفحه تنظیمات پیاده می‌شود. |
| **سوءاستفاده از هویت** | هشدار قانونی در UI، ثبت لاگ کامل (IP، user-agent، زمان) |
| **استفاده از AI قبل از احراز هویت** | تمام اندپوینت‌های هوش مصنوعی نیاز به توکن سطح ۲ یا ۳ دارند. در این مرحله هیچ AIای در دسترس نیست. |

---

### ۶. جریان داده و وضعیت‌ها

| مرحله | وضعیت کاربر در دیتابیس | توکن صادر شده | اقدام بعدی |
|--------|------------------------|----------------|-------------|
| کاربر جدید، OTP تأیید شد | رکورد در `users` | سطح ۱ (level 1) | هدایت به صفحه «درخواست نقش اولیه» |
| کاربر قدیمی، یک اکانت دارد | رکورد + یک ردیف در `accounts` | سطح ۱ (level 1) | هدایت به داشبورد آن اکانت |
| کاربر قدیمی، چند اکانت دارد | رکورد + چند ردیف در `accounts` | سطح ۱ (level 1) | هدایت به صفحه «انتخاب اکانت» |

---

### ۷. ملاحظات اضافی (تطابق با توضیحات شما)

- **تنها یک صفحه برای ورود و ثبت‌نام** وجود دارد. تفاوت فقط در پاسخ بک‌اند است.
- **هیچ رمز عبوری** نه در کلاینت و نه در سرور ذخیره یا استفاده نمی‌شود.
- **کد ملی** صرفاً ۱۰ رقم و با الگوریتم کنترل صحت.
- **پیش‌شماره موبایل** به صورت یک کامبوی تک انتخابی (فعلاً +98 ایران). در آینده قابل گسترش است.
- **هشدار سواستفاده** به صورت برجسته در پایین صفحه درج شده است.

---

### ۸. خروجی نهایی (صفحه)

```
هوشیاد

کد ملی (۱۰ رقم): [۱۲۳۴۵۶۷۸۹۰]

شماره موبایل: [🇮🇷 +98] [۹۱۲۳۴۵۶۷۸۹]

[ارسال کد تأیید]

(پس از دریافت کد)
کد تأیید ۶ رقمی: [ _ _ _ _ _ _ ]

[ورود / ثبت‌نام]

⚠️ وارد کردن اطلاعات نادرست و استفاده از هویت دیگران پیگرد قانونی دارد.
```

---

## ✅ تأیید نهایی

این طراحی **کامل** است. تمام جزئیات منطق فرانت‌اند، بک‌اند، ساختار داده، امنیت و کامپوننت‌ها درج شده است. 