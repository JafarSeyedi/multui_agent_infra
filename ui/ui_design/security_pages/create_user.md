## ✅ صفحه ثبت‌نام کاربر جدید (Register New User)

این صفحه برای افزودن یک **کاربر جدید (شخص حقیقی)** به سامانه و دستگاه فعلی استفاده می‌شود. کاربر جدید با وارد کردن **نام، نام خانوادگی، کد ملی** ثبت‌نام می‌شود. در این مرحله **اکانتی ساخته نمی‌شود** و کاربر تازه ثبت‌نام‌شده **هیچ اکانتی ندارد**. پس از ثبت‌نام موفق، پیام نمایش داده می‌شود که کد ملی باید تأیید شود و راه‌های تأیید (بارگذاری مدارک، معرفی توسط معلم/مدیر مدرسه/مدیر مؤسسه و ...) به کاربر نمایش داده می‌شود. کاربر سپس می‌تواند به صفحه **ایجاد حساب جدید** (Create Account) برود تا اولین اکانت خود را درخواست کند.

**نکات کلیدی:**
- یکتایی کد ملی در سامانه بررسی می‌شود.
- شماره موبایل در این مرحله گرفته نمی‌شود (بعداً در فرآیند احراز هویت اضافه می‌شود).
- پس از ثبت‌نام، رکوردی در جدول `users` با وضعیت `phone_verified_at = NULL` و `national_id_verified_at = NULL` ایجاد می‌شود.
- کاربر از طریق لینک «بارگذاری مدارک شناسایی» می‌تواند برای تأیید کد ملی اقدام کند. همچنین راه‌های معرفی توسط معلم، مدیر مدرسه، مدیر مؤسسه و ... توضیح داده می‌شود.

---

## ۱. رابط کاربری (UI)

```
┌─────────────────────────────────────────────────────────────┐
│                   ثبت‌نام کاربر جدید                        │
├─────────────────────────────────────────────────────────────┤
│ نام: [__________________________]                           │
│ نام خانوادگی: [_________________]                          │
│ کد ملی (۱۰ رقم): [__________]                              │
│                                                             │
│ [ثبت‌نام]                                                   │
│                                                             │
│ (پس از ثبت‌نام موفق)                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ✅ کاربر با موفقیت ثبت شد.                            │ │
│ │                                                         │ │
│ │ ⚠️ کد ملی شما هنوز تأیید نشده است. برای دسترسی به   │ │
│ │    امکانات سامانه، باید کد ملی خود را تأیید کنید.    │ │
│ │                                                          │ │
│ │ راه‌های تأیید کد ملی:                                   │ │
│ │ • بارگذاری مدارک شناسایی (کارت ملی، شناسنامه)         │ │
│ │ • معرفی توسط معلم / مدیر مدرسه یا مؤسسه آموزشی        │ │
│ │ • احراز هویت از طریق سامانه «دولت من»                 │ │
│ │                                                         │ │
│ │ [بارگذاری مدارک]  [بعداً]                              │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ [بستن]                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## ۲. کامپوننت‌ها (UI Components)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `FormContainer` | View | محفظه فرم ثبت‌نام |
| `FirstNameInput` | TextInput | فیلد ورودی نام |
| `LastNameInput` | TextInput | فیلد ورودی نام خانوادگی |
| `NationalIdInput` | TextInput | فیلد کد ملی (۱۰ رقم، عددی، اعتبارسنجی) |
| `RegisterButton` | TouchableOpacity | دکمه ثبت‌نام (فعال پس از پر شدن فرم) |
| `SuccessMessageCard` | View | کارت نمایش پیام موفقیت (پس از ثبت‌نام) |
| `VerificationOptionsList` | FlatList | لیست راه‌های تأیید کد ملی (متن و آیکون) |
| `UploadDocumentsLink` | TouchableOpacity | لینک به صفحه بارگذاری مدارک |
| `LaterButton` | TouchableOpacity | دکمه «بعداً» (بستن مودال و بازگشت) |
| `CloseButton` | TouchableOpacity | بستن صفحه (در حالت عادی) |

---

## ۳. منطق فرانت‌اند (React Native + Expo)

### ۳.۱. State و توابع

```tsx
// screens/RegisterNewUserScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator, ScrollView } from 'react-native';
import { api } from '../services/api';
import { storeToken } from '../utils/storage';
import { getLocalUsers, saveLocalUsers, setCurrentUserAndAccount } from '../utils/localUserStorage';

export default function RegisterNewUserScreen({ navigation }) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);
  const [newUserId, setNewUserId] = useState(null);

  const validateNationalId = (id: string) => {
    if (!/^\d{10}$/.test(id)) return false;
    // الگوریتم کنترل کد ملی (اختیاری)
    let sum = 0;
    for (let i = 0; i < 9; i++) sum += parseInt(id[i]) * (10 - i);
    const remainder = sum % 11;
    const control = parseInt(id[9]);
    return (remainder < 2 && control === remainder) || (remainder >= 2 && control === 11 - remainder);
  };

  const handleRegister = async () => {
    if (!firstName.trim()) { Alert.alert('خطا', 'لطفاً نام را وارد کنید'); return; }
    if (!lastName.trim()) { Alert.alert('خطا', 'لطفاً نام خانوادگی را وارد کنید'); return; }
    if (!validateNationalId(nationalId)) { Alert.alert('خطا', 'کد ملی ۱۰ رقم معتبر نیست'); return; }
    setLoading(true);
    try {
      const res = await api.post('/auth/register-user', { firstName, lastName, nationalId });
      setNewUserId(res.data.userId);
      setRegistered(true);
      // به‌روزرسانی کش محلی (اضافه کردن کاربر جدید به لیست کاربران دستگاه)
      await addUserToLocalCache(res.data.userId, firstName + ' ' + lastName, nationalId);
    } catch (err: any) {
      if (err.response?.status === 409) {
        Alert.alert('خطا', 'کد ملی قبلاً ثبت شده است. در صورت تعلق به شما، از صفحه ورود استفاده کنید.');
      } else {
        Alert.alert('خطا', 'ثبت‌نام انجام نشد. لطفاً دوباره تلاش کنید.');
      }
    } finally {
      setLoading(false);
    }
  };

  const addUserToLocalCache = async (userId, fullName, nationalId) => {
    const local = await getLocalUsers();
    const existing = local.users.find(u => u.nationalId === nationalId);
    if (!existing) {
      local.users.push({
        nationalId: nationalId,
        fullName: fullName,
        phone: '', // شماره موبایل بعداً اضافه می‌شود (در فرآیند احراز هویت)
        accounts: [], // هنوز اکانتی ندارد
      });
      await saveLocalUsers(local);
    }
  };

  const goToUploadDocuments = () => {
    navigation.navigate('NationalIdVerification', { userId: newUserId });
  };

  const goToCreateAccount = () => {
    // کاربر جدید اکنون ثبت شده، می‌تواند اولین اکانت خود را ایجاد کند
    navigation.replace('CreateAccount', { forUserId: newUserId });
  };

  if (registered) {
    return (
      <ScrollView style={{ padding: 20, backgroundColor: '#fff', flex: 1 }}>
        <View style={{ marginTop: 50, alignItems: 'center' }}>
          <Text style={{ fontSize: 28, color: '#4caf50', marginBottom: 16 }}>✅ ثبت‌نام موفق</Text>
          <Text style={{ fontSize: 16, textAlign: 'center', marginBottom: 20 }}>
            کاربر {firstName} {lastName} با کد ملی {nationalId} ثبت شد.
          </Text>
          <View style={{ backgroundColor: '#fff9c4', padding: 16, borderRadius: 12, marginVertical: 16, borderWidth: 1, borderColor: '#f0ad4e' }}>
            <Text style={{ fontWeight: 'bold', marginBottom: 8 }}>⚠️ کد ملی شما هنوز تأیید نشده است.</Text>
            <Text style={{ marginBottom: 12 }}>برای دسترسی به امکانات سامانه، باید کد ملی خود را تأیید کنید.</Text>
            <Text style={{ fontWeight: 'bold', marginBottom: 4 }}>راه‌های تأیید کد ملی:</Text>
            <Text>• بارگذاری مدارک شناسایی (کارت ملی، شناسنامه)</Text>
            <Text>• معرفی توسط معلم / مدیر مدرسه</Text>
            <Text>• معرفی توسط مدیر مؤسسه آموزشی</Text>
            <Text>• احراز هویت از طریق سامانه «دولت من»</Text>
          </View>
          <TouchableOpacity onPress={goToUploadDocuments} style={{ backgroundColor: '#0066cc', padding: 12, borderRadius: 8, width: '80%', alignItems: 'center', marginBottom: 12 }}>
            <Text style={{ color: '#fff', fontWeight: 'bold' }}>بارگذاری مدارک</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={goToCreateAccount} style={{ backgroundColor: '#4caf50', padding: 12, borderRadius: 8, width: '80%', alignItems: 'center', marginBottom: 12 }}>
            <Text style={{ color: '#fff', fontWeight: 'bold' }}>ایجاد حساب (اکانت) جدید</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 12 }}>
            <Text style={{ color: '#888' }}>بعداً</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={{ padding: 20, backgroundColor: '#fff', flex: 1 }}>
      <Text style={{ fontSize: 28, textAlign: 'center', marginVertical: 20 }}>ثبت‌نام کاربر جدید</Text>
      <TextInput placeholder="نام" value={firstName} onChangeText={setFirstName} style={inputStyle} />
      <TextInput placeholder="نام خانوادگی" value={lastName} onChangeText={setLastName} style={inputStyle} />
      <TextInput placeholder="کد ملی (۱۰ رقم)" value={nationalId} onChangeText={setNationalId} keyboardType="number-pad" maxLength={10} style={inputStyle} />
      <TouchableOpacity onPress={handleRegister} disabled={loading} style={{ backgroundColor: '#0066cc', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 20 }}>
        <Text style={{ color: '#fff', fontWeight: 'bold' }}>{loading ? 'در حال ثبت‌نام...' : 'ثبت‌نام'}</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginTop: 20, alignItems: 'center', padding: 10 }}>
        <Text style={{ color: '#888' }}>بازگشت</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const inputStyle = {
  borderWidth: 1,
  borderColor: '#ccc',
  borderRadius: 8,
  padding: 12,
  marginVertical: 8,
  fontSize: 16,
};
```

---

## ۴. منطق بک‌اند (FastAPI + PostgreSQL)

### ۴.۱. مدل داده (قبلاً تعریف شده)

جدول `users` تغییر نمی‌کند. فقط فیلد `full_name` اضافه شده است (یا می‌توان از `first_name` و `last_name` جداگانه استفاده کرد). فرض می‌کنیم:

```sql
ALTER TABLE users ADD COLUMN first_name VARCHAR(50);
ALTER TABLE users ADD COLUMN last_name VARCHAR(50);
```

### ۴.۲. API ثبت‌نام کاربر جدید

#### `POST /auth/register-user`

- **بدن:** `{ firstName, lastName, nationalId }`
- **عملیات:**
  1. اعتبارسنجی کد ملی (فرمت، الگوریتم).
  2. بررسی یکتایی کد ملی در جدول `users`.
  3. اگر تکراری نبود، رکورد جدید در `users` ایجاد می‌شود با:
     - `national_id`
     - `first_name`, `last_name`
     - `phone = NULL`
     - `phone_verified_at = NULL`
     - `national_id_verified_at = NULL`
  4. **هیچ اکانتی ساخته نمی‌شود.**
  5. تولید یک **توکن موقت** (سطح مقدماتی) برای کاربر جدید؟ نیازی نیست، زیرا هنوز لاگین نکرده است. اما برای ادامه فرآیند (بارگذاری مدارک) نیاز به احراز هویت داریم. بهتر است بعد از ثبت‌نام، کاربر را به صفحه ورود هدایت کنیم تا با کد ملی (و شماره موبایل بعداً) وارد شود. اما طبق درخواست شما، کاربر جدید مستقیماً بعد از ثبت‌نام در دستگاه ذخیره می‌شود و می‌تواند بدون لاگین مجدد اقدام به بارگذاری مدارک کند. برای این کار، یک **توکن کوتاه مدت** برای کاربر جدید صادر می‌کنیم (مخصوص این جلسه). یا ساده‌تر: در فرانت‌اند پس از ثبت‌نام، کاربر را به صفحه بارگذاری مدارک می‌بریم و در آن صفحه، userId ذخیره شده را به عنوان پارامتر ارسال می‌کنیم. API بارگذاری مدارک باید userId را دریافت کند و بررسی کند که این userId متعلق به همان کاربر (با IP و نشست) است. برای امنیت بیشتر، می‌توان یک توکن یکبار مصرف برای عملیات بارگذاری مدارک صادر کرد.

**پاسخ ساده (بدون توکن):**
```json
{ "message": "user registered", "userId": "uuid" }
```

**امنیت:** ریسک پایین است زیرا مدارک بعداً توسط مدیر بررسی می‌شود. اما برای جلوگیری از سوءاستفاده، می‌توان درخواست بارگذاری مدارک را به IP محدود کرد یا از توکن موقت استفاده کرد.

---

## ۵. ملاحظات امنیتی

| نیاز | راهکار |
|------|--------|
| **یکتایی کد ملی** | بررسی در دیتابیس (unique constraint) قبل از درج |
| **اعتبارسنجی کد ملی** | هم سمت کلاینت و هم سمت سرور (الگوریتم mod 11) |
| **جلوگیری از ثبت‌نام بدون شماره موبایل** | شماره موبایل در این مرحله اختیاری نیست؟ طبق طراحی، در مرحله ثبت‌نام کاربر جدید، شماره موبایل گرفته نمی‌شود. بعداً در فرآیند تأیید هویت اضافه می‌شود. این تصمیم صحیح است زیرا ممکن است کاربر شماره موبایل خود را بعداً ارائه دهد. اما برای احراز هویت سطح 1، شماره موبایل ضروری است. پس باید در صفحه بارگذاری مدارک یا در مرحله بعد، شماره موبایل نیز گرفته شود. در این صفحه فقط کد ملی و نام ثبت می‌شود. |
| **دسترسی به ثبت‌نام** | این صفحه عمومی است (نیاز به احراز هویت ندارد). اما باید نرخ محدودیت (rate limit) برای جلوگیری از ثبت‌نام انبوه اعمال شود: هر IP حداکثر ۵ بار در روز. |

---

## ۶. نمایش راه‌های تأیید کد ملی

در صفحه موفقیت، راه‌های تأیید به صورت لیست نمایش داده می‌شود. هر راه می‌تواند به صفحه یا توضیحات جداگانه لینک شود.

- **بارگذاری مدارک:** لینک به صفحه `NationalIdVerification` (که تصاویر کارت ملی، شناسنامه و فیلم دریافت می‌کند).
- **معرفی توسط معلم / مدیر مدرسه / مدیر مؤسسه:** توضیح داده می‌شود که این افراد می‌توانند از طریق پنل خود، برای کاربر درخواست تأیید کد ملی ارسال کنند.
- **احراز هویت از طریق دولت من:** لینک به درگاه ملی (در صورتی که پیاده‌سازی شده باشد).

---

## ۷. تکمیل جریان: پس از ثبت‌نام

کاربر جدید گزینه‌های زیر را دارد:
1. **بارگذاری مدارک** → رفتن به صفحه تأیید کد ملی (سطح ۲).
2. **ایجاد حساب (اکانت) جدید** → رفتن به صفحه CreateAccount (برای درخواست نقش اصلی).
3. **بعداً** → بستن صفحه و بازگشت به صفحه سوئیچ کاربر/حساب (کاربر جدید در لیست کاربران دستگاه اضافه شده اما هنوز اکانتی ندارد).

---

## ۸. خروجی نهایی

این صفحه تمام نیازهای شما را پوشش می‌دهد:
- ثبت‌نام کاربر جدید با نام، نام خانوادگی، کد ملی.
- بررسی یکتایی کد ملی.
- نمایش پیام موفقیت و اخطار عدم تأیید کد ملی.
- نمایش لیست راه‌های تأیید کد ملی با لینک بارگذاری مدارک.
- امکان ایجاد حساب جدید (اکانت) پس از ثبت‌نام.
- استفاده در بافت دستگاه (ذخیره در کش محلی) و امکان سوئیچ به این کاربر بعداً (پس از تکمیل اطلاعات).

در صورت تأیید، صفحه **بارگذاری مدارک (تأیید کد ملی)** را طراحی خواهم کرد.