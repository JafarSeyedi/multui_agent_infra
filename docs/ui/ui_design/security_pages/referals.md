## ✅ صفحه معرفی کاربر به سامانه (برای مدیران و معلمان)

این صفحه به **مدیر مدرسه، مدیر مؤسسه آموزشی و معلمان** اجازه می‌دهد کاربران دیگر (معلم، دانش‌آموز، والدین) را به سامانه معرفی کنند. معرفی شدن به معنی اعطای نقش (و در صورت لزوم تأیید کد ملی) است. شخص معرفی‌شده **قبلاً باید در سامانه ثبت‌نام کرده باشد** (حساب کاربری داشته باشد) و **اکانت مناسب** (نقش اصلی مورد نظر) را ایجاد کرده باشد (یا همزمان ایجاد کند). در صورت عدم تطابق اطلاعات یا عدم وجود کاربر، خطای مناسب نمایش داده می‌شود. همچنین برای معرفی والدین، نیاز به کد ملی دانش‌آموز و شرط وابستگی به مدرسه/کلاس/معلم وجود دارد.

**نکات کلیدی:**
- معرفی‌کننده باید دارای نقش مجاز باشد (مدیر مدرسه، مدیر مؤسسه، معلم).
- اطلاعات فرد معرفی‌شونده (نام، نام خانوادگی، کد ملی، شماره موبایل) با اطلاعات ثبت‌نام‌شده در سامانه تطابق داده می‌شود.
- اگر کد ملی معرفی‌شونده قبلاً تأیید نشده باشد، با این معرفی **تأیید خودکار** می‌شود (سطح ۲ احراز هویت).
- نقش معرفی‌شده مشخص می‌شود (معلم، دانش‌آموز، والدین). ممکن است نیاز به اطلاعات تکمیلی مانند کلاس، درس، دوره، مدرسه باشد که بر اساس همان context (مثلاً کلاسی که معرفی‌کننده در آن نقش دارد) تعیین می‌شود.
- در معرفی والدین، کد ملی دانش‌آموز نیز وارد می‌شود. شرط: دانش‌آموز قبلاً نقش دانش‌آموز در همان مدرسه (یا همان کلاس یا زیر نظر همان معلم) را داشته باشد (وابستگی به context معرفی‌کننده).

---

## ۱. رابط کاربری (UI)

```
┌─────────────────────────────────────────────────────────────┐
│                   معرفی کاربر به سامانه                     │
├─────────────────────────────────────────────────────────────┤
│ نقش مورد نظر:                                              │
│ ○ معلم    ○ دانش‌آموز    ○ والدین                          │
├─────────────────────────────────────────────────────────────┤
│ نام: [__________________________]                          │
│ نام خانوادگی: [_________________]                          │
│ کد ملی: [__________]                                       │
│ شماره موبایل (با پیش‌شماره): [🇮🇷 +98] [__________]        │
├─────────────────────────────────────────────────────────────┤
│ (شرط: در صورت انتخاب نقش والدین)                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ کد ملی دانش‌آموز: [__________]                         │ │
│ │ (دانش‌آموز باید قبلاً در این مدرسه/کلاس نقش داشته باشد)│ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ [بررسی و معرفی]                                            │
│                                                             │
│ ⚠️ توجه: شخص معرفی‌شونده باید قبلاً در سامانه ثبت‌نام کرده │
│    و حساب کاربری (اکانت) داشته باشد.                       │
│    در صورت تطابق اطلاعات، نقش مورد نظر اعطا می‌شود.        │
└─────────────────────────────────────────────────────────────┘
```

### پس از موفقیت (نمایش پیام):

```
┌─────────────────────────────────────────────────────────────┐
│                      ✅ معرفی موفق                          │
├─────────────────────────────────────────────────────────────┤
│ کاربر علی رضایی با نقش معلم با موفقیت معرفی شد.           │
│                                                             │
│ در صورت عدم تأیید قبلی کد ملی، اکنون تأیید شد.             │
│                                                             │
│ [بازگشت به صفحه مدیریت]  [معرفی مجدد]                     │
└─────────────────────────────────────────────────────────────┘
```

---

## ۲. کامپوننت‌ها (UI Components)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `RoleSelector` | RadioGroup | انتخاب نقش: معلم، دانش‌آموز، والدین |
| `NameInput` | TextInput | نام |
| `LastNameInput` | TextInput | نام خانوادگی |
| `NationalIdInput` | TextInput | کد ملی (۱۰ رقم) |
| `PhoneInput` | TextInput + PhonePrefix | شماره موبایل با پیش‌شماره (+98) |
| `ChildNationalIdInput` | TextInput | (شرطی) کد ملی دانش‌آموز (برای نقش والدین) |
| `SubmitButton` | TouchableOpacity | دکمه بررسی و معرفی |
| `SuccessMessage` | View | پیام موفقیت |
| `ErrorMessage` | Text | نمایش خطاها |

---

## ۳. منطق فرانت‌اند (React Native + Expo)

```tsx
// screens/ReferUserScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { api } from '../services/api';

type Role = 'teacher' | 'student' | 'parent';

export default function ReferUserScreen({ navigation }) {
  const [role, setRole] = useState<Role>('teacher');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [phonePrefix, setPhonePrefix] = useState('+98');
  const [phone, setPhone] = useState('');
  const [childNationalId, setChildNationalId] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const validateNationalId = (id: string) => {
    if (!/^\d{10}$/.test(id)) return false;
    // الگوریتم کنترل (اختیاری)
    let sum = 0;
    for (let i = 0; i < 9; i++) sum += parseInt(id[i]) * (10 - i);
    const remainder = sum % 11;
    const control = parseInt(id[9]);
    return (remainder < 2 && control === remainder) || (remainder >= 2 && control === 11 - remainder);
  };

  const handleSubmit = async () => {
    if (!firstName.trim()) { Alert.alert('خطا', 'نام را وارد کنید'); return; }
    if (!lastName.trim()) { Alert.alert('خطا', 'نام خانوادگی را وارد کنید'); return; }
    if (!validateNationalId(nationalId)) { Alert.alert('خطا', 'کد ملی ۱۰ رقم معتبر نیست'); return; }
    const fullPhone = phonePrefix + phone;
    if (!phone || phone.length < 10) { Alert.alert('خطا', 'شماره موبایل معتبر نیست'); return; }
    if (role === 'parent' && (!childNationalId || !validateNationalId(childNationalId))) {
      Alert.alert('خطا', 'کد ملی دانش‌آموز معتبر نیست');
      return;
    }
    setLoading(true);
    try {
      const payload: any = {
        role,
        firstName,
        lastName,
        nationalId,
        phone: fullPhone,
      };
      if (role === 'parent') {
        payload.childNationalId = childNationalId;
      }
      await api.post('/referrals', payload);
      setSuccess(true);
    } catch (err: any) {
      let errorMsg = 'معرفی انجام نشد.';
      if (err.response?.status === 404) {
        errorMsg = 'کاربر با این اطلاعات یافت نشد. لطفاً مطمئن شوید کاربر قبلاً ثبت‌نام کرده است.';
      } else if (err.response?.status === 409) {
        errorMsg = 'این کاربر قبلاً با این نقش معرفی شده است.';
      } else if (err.response?.status === 400) {
        errorMsg = err.response.data?.error || 'اطلاعات مغایرت دارد.';
      }
      Alert.alert('خطا', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <ScrollView style={{ padding: 20, backgroundColor: '#fff', flex: 1 }}>
        <View style={{ alignItems: 'center', marginTop: 50 }}>
          <Text style={{ fontSize: 28, color: '#4caf50', marginBottom: 16 }}>✅ معرفی موفق</Text>
          <Text style={{ textAlign: 'center', marginVertical: 16 }}>
            کاربر {firstName} {lastName} با نقش {role === 'teacher' ? 'معلم' : role === 'student' ? 'دانش‌آموز' : 'والدین'} با موفقیت معرفی شد.
            {role === 'parent' && ' همچنین رابطه والدینی با دانش‌آموز ثبت شد.'}
          </Text>
          <TouchableOpacity onPress={() => navigation.goBack()} style={{ backgroundColor: '#0066cc', padding: 12, borderRadius: 8, width: '80%', alignItems: 'center', marginTop: 10 }}>
            <Text style={{ color: '#fff' }}>بازگشت به صفحه مدیریت</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => setSuccess(false)} style={{ padding: 12, marginTop: 10 }}>
            <Text style={{ color: '#888' }}>معرفی مجدد</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={{ padding: 20, backgroundColor: '#fff', flex: 1 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginVertical: 20 }}>معرفی کاربر به سامانه</Text>
      
      <Text style={{ marginVertical: 8 }}>نقش مورد نظر:</Text>
      <View style={{ flexDirection: 'row', marginBottom: 20 }}>
        <TouchableOpacity onPress={() => setRole('teacher')} style={{ flexDirection: 'row', alignItems: 'center', marginRight: 20 }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: role === 'teacher' ? '#0066cc' : '#fff' }} />
          <Text>معلم</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setRole('student')} style={{ flexDirection: 'row', alignItems: 'center', marginRight: 20 }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: role === 'student' ? '#0066cc' : '#fff' }} />
          <Text>دانش‌آموز</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setRole('parent')} style={{ flexDirection: 'row', alignItems: 'center' }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: role === 'parent' ? '#0066cc' : '#fff' }} />
          <Text>والدین</Text>
        </TouchableOpacity>
      </View>

      <TextInput placeholder="نام" value={firstName} onChangeText={setFirstName} style={inputStyle} />
      <TextInput placeholder="نام خانوادگی" value={lastName} onChangeText={setLastName} style={inputStyle} />
      <TextInput placeholder="کد ملی (۱۰ رقم)" value={nationalId} onChangeText={setNationalId} keyboardType="number-pad" maxLength={10} style={inputStyle} />
      <View style={{ flexDirection: 'row', alignItems: 'center', marginVertical: 8 }}>
        <TextInput value={phonePrefix} editable={false} style={{ width: 50, borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12, marginRight: 8 }} />
        <TextInput placeholder="۹۱۲۳۴۵۶۷۸۹" value={phone} onChangeText={setPhone} keyboardType="number-pad" maxLength={10} style={{ flex: 1, borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12 }} />
      </View>

      {role === 'parent' && (
        <View style={{ marginVertical: 8 }}>
          <TextInput placeholder="کد ملی دانش‌آموز" value={childNationalId} onChangeText={setChildNationalId} keyboardType="number-pad" maxLength={10} style={inputStyle} />
          <Text style={{ fontSize: 12, color: '#666', marginTop: 4 }}>دانش‌آموز باید قبلاً در این مدرسه/کلاس نقش داشته باشد.</Text>
        </View>
      )}

      <TouchableOpacity onPress={handleSubmit} disabled={loading} style={{ backgroundColor: '#4caf50', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 20 }}>
        <Text style={{ color: '#fff', fontWeight: 'bold' }}>{loading ? 'در حال بررسی...' : 'بررسی و معرفی'}</Text>
      </TouchableOpacity>

      <Text style={{ fontSize: 12, color: '#888', textAlign: 'center', marginTop: 20 }}>
        ⚠️ شخص معرفی‌شونده باید قبلاً در سامانه ثبت‌نام کرده باشد. در صورت تطابق اطلاعات، نقش مورد نظر اعطا می‌شود و در صورت نیاز کد ملی تأیید می‌گردد.
      </Text>
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

### ۴.۱. مدل داده (جدول referrals)

```sql
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_user_id UUID NOT NULL REFERENCES users(id), -- شخص معرفی‌کننده
    referred_user_id UUID NOT NULL REFERENCES users(id), -- شخص معرفی‌شونده
    role VARCHAR(50) NOT NULL, -- 'teacher', 'student', 'parent'
    context_id UUID, -- در صورت نیاز: کلاس، مدرسه، دوره، ...
    child_student_id UUID, -- برای نقش والدین، ارجاع به دانش‌آموز
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(referred_user_id, role, context_id) -- جلوگیری از معرفی تکراری
);
```

### ۴.۲. API معرفی

#### `POST /referrals`

- **نیاز به توکن سطح ۱ (معرفی‌کننده باید احراز هویت شده باشد)**
- **بدن:** 
```json
{
  "role": "teacher" | "student" | "parent",
  "firstName": "علی",
  "lastName": "رضایی",
  "nationalId": "1234567890",
  "phone": "+989123456789",
  "childNationalId": "0987654321" // فقط برای نقش parent
}
```
- **مراحل پردازش:**
  1. بررسی مجوز معرفی‌کننده: بر اساس نقش اصلی و نقش‌های تابعه‌اش در دیتابیس، آیا حق معرفی این نقش را دارد؟ (مثلاً مدیر مدرسه می‌تواند معلم، دانش‌آموز، والدین را معرفی کند؛ معلم می‌تواند دانش‌آموز و والدین را معرفی کند؛ مدیر مؤسسه مشابه).
  2. جستجوی کاربر در جدول `users` با فیلدهای `first_name`, `last_name`, `national_id`, `phone`. اگر کاربری یافت نشد → پاسخ `404`.
  3. اگر کاربر یافت شد اما اطلاعات نام، نام خانوادگی، شماره موبایل با درخواست مطابقت نداشت → پاسخ `400` با خطای اطلاعات مغایر.
  4. بررسی وجود معرفی قبلی برای این کاربر با همان نقش در همان context (context از روی معرفی‌کننده استخراج می‌شود: مثلاً معرفی‌کننده مدیر مدرسه خاص است → context_id همان مدرسه). اگر قبلاً معرفی شده بود → پاسخ `409`.
  5. اگر نقش `parent` است:
     - جستجوی دانش‌آموز با `childNationalId`.
     - بررسی اینکه دانش‌آموز در همان مدرسه (یا کلاس یا زیر نظر همان معلم) نقش دارد. شرط: معرفی‌کننده باید دارای نقشی باشد که بر آن دانش‌آموز نظارت دارد (مدیر مدرسه، معلم آن کلاس/درس). اگر شرط برقرار نبود → پاسخ `400` با خطای «دانش‌آموز تحت نظارت شما نیست».
  6. اگر همه موارد تأیید شد:
     - اضافه کردن نقش مربوطه به اکانت کاربر معرفی‌شونده (در جدول `account_secondary_roles`). برای نقش معلم، نیاز به اکانت با نقش اصلی `teacher` دارد. اگر کاربر چنین اکانتی ندارد، ابتدا باید اکانت ایجاد کند (اما معرفی در این مرحله فقط نقش تابعه را اضافه می‌کند و اکانت اصلی را ایجاد نمی‌کند. بهتر است شرط کنیم که کاربر قبلاً اکانت اصلی مناسب را ایجاد کرده باشد. اگر نداشته باشد، معرفی با خطا مواجه می‌شود و پیام «ابتدا اکانت خود را ایجاد کنید» نمایش داده می‌شود).
     - اگر کاربر قبلاً تأیید کد ملی (national_id_verified_at) ندارد، این فیلد را به `now()` به‌روزرسانی کنید (تأیید خودکار).
     - ذخیره رکورد در جدول `referrals`.
  7. پاسخ موفق: `{ message: "user referred successfully" }`

**نکته مهم در مورد اکانت‌ها:** معرفی فقط نقش‌های تابعه را اضافه می‌کند. کاربر معرفی‌شونده باید قبلاً اکانتی با نقش اصلی مناسب (مثلاً `teacher` برای نقش معلم، `student` برای دانش‌آموز، `parent` برای والدین) ایجاد کرده باشد. اگر نداشته باشد، معرفی با خطا مواجه می‌شود و پیام «لطفاً ابتدا اکانت خود را ایجاد کنید» نمایش داده می‌شود. این منطق در سرویس بک‌اند پیاده می‌شود.

---

## ۵. ملاحظات امنیتی

| تهدید | راهکار |
|--------|--------|
| معرفی توسط افراد غیرمجاز | بررسی نقش معرفی‌کننده در بک‌اند (بر اساس token و نقش‌های او) |
| تطابق اطلاعات | جستجوی دقیق کاربر بر اساس نام، نام خانوادگی، کد ملی، شماره موبایل (همه فیلدها) |
| جلوگیری از معرفی تکراری | unique constraint در دیتابیس |
| دستکاری درخواست برای دیگران | معرفی‌کننده فقط می‌تواند برای کاربران دیگر درخواست دهد (نمی‌تواند خود را معرفی کند) – بررسی که `referred_user_id` برابر با `referrer_user_id` نباشد. |
| شرط والدین | بررسی دقیق وجود دانش‌آموز و رابطه نظارتی معرفی‌کننده با او (بر اساس context) |

---

## ۶. خروجی نهایی

این صفحه تمام نیازهای شما را پوشش می‌دهد:
- انتخاب نقش (معلم، دانش‌آموز، والدین)
- وارد کردن اطلاعات معرفی‌شونده (نام، نام خانوادگی، کد ملی، شماره موبایل)
- برای والدین: کد ملی دانش‌آموز و شرط نظارت
- تطابق کامل اطلاعات با ثبت‌نام قبلی
- تأیید خودکار کد ملی در صورت عدم تأیید قبلی
- جلوگیری از معرفی تکراری
- خطاهای واضح در صورت عدم وجود کاربر، مغایرت اطلاعات، عدم وجود اکانت مناسب

