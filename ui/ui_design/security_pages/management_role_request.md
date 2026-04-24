## ✅ صفحه بارگذاری مدارک برای تأیید نقش مدیر مدرسه خاص / مدیر مؤسسه آموزشی خاص

این صفحه به کاربرانی که نقش **مدیر مدرسه خاص** یا **مدیر مؤسسه آموزشی خاص** را درخواست کرده‌اند (یا قصد دارند این نقش را دریافت کنند) اجازه می‌دهد مدارک مورد نیاز را بارگذاری کنند. مدارک شامل **نامه معرفی با سربرگ و مهر مدرسه/مؤسسه** است که در آن نام و نام خانوادگی، شماره همراه و کد ملی نماینده/مدیر درج شده باشد. پس از بارگذاری، مدارک توسط **پشتیبان سامانه** بررسی می‌شود و در صورت تأیید، نقش مربوطه به اکانت کاربر اضافه می‌شود.

**نکات کلیدی:**
- این صفحه فقط کاربرانی که قبلاً اکانت با نقش اصلی «مدیر مدرسه» یا «مدیر مؤسسه آموزشی» را درخواست کرده‌اند (یا قرار است درخواست کنند) استفاده می‌کنند. اما می‌تواند برای هر کاربری که قصد اخذ این نقش را دارد باز باشد.
- مدارک باید شامل **نامه رسمی با سربرگ و مهر** باشد.
- اطلاعات معرفی‌شده در نامه (نام، نام خانوادگی، شماره موبایل، کد ملی) باید با اطلاعات کاربر ثبت‌نام‌شده در سامانه مطابقت داشته باشد (بررسی خودکار AI یا دستی توسط پشتیبان).
- پس از تأیید، نقش «مدیر مدرسه خاص» یا «مدیر مؤسسه آموزشی خاص» به اکانت کاربر اضافه می‌شود (و در صورت نیاز، اکانت اصلی نیز ایجاد می‌گردد).

---

## ۱. رابط کاربری (UI)

```
┌─────────────────────────────────────────────────────────────┐
│        بارگذاری مدارک برای تأیید نقش مدیریت                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ نوع نقش درخواستی:                                          │
│ ○ مدیر مدرسه خاص                                           │
│ ○ مدیر مؤسسه آموزشی خاص                                    │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📄 نامه معرفی (با سربرگ و مهر)                         │ │
│ │                                                         │ │
│ │ نامه باید شامل اطلاعات زیر باشد:                       │ │
│ │ • نام و نام خانوادگی نماینده/مدیر                      │ │
│ │ • شماره همراه                                           │ │
│ │ • کد ملی                                                 │ │
│ │                                                         │ │
│ │ [انتخاب فایل] (jpg, png, pdf - حداکثر ۵ مگابایت)      │ │
│ │                                                         │ │
│ │ (پس از انتخاب) ✅ فایل انتخاب شد: letter.pdf           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [ثبت درخواست]                                              │
│                                                             │
│ ⚠️ مدارک ارسالی توسط پشتیبان سامانه بررسی می‌شود.         │
│    در صورت تأیید، نقش مدیریت به حساب شما اضافه می‌شود.    │
│                                                             │
│ [بازگشت]                                                   │
└─────────────────────────────────────────────────────────────┘
```

### پس از ارسال موفق (حالت موفقیت)

```
┌─────────────────────────────────────────────────────────────┐
│                    درخواست شما ثبت شد                       │
├─────────────────────────────────────────────────────────────┤
│ ✅ مدارک با موفقیت ارسال شد.                               │
│                                                             │
│ شماره پیگیری: REQ-123456                                   │
│                                                             │
│ وضعیت: در انتظار بررسی (حداکثر ۲ روز کاری)                │
│                                                             │
│ پس از تأیید، نقش مدیریت به حساب شما اضافه خواهد شد.       │
│                                                             │
│ [مشاهده وضعیت درخواست]  [بازگشت]                          │
└─────────────────────────────────────────────────────────────┘
```

---

## ۲. کامپوننت‌ها (UI Components)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `FormContainer` | View | محفظه اصلی فرم |
| `RoleTypeSelector` | RadioGroup | انتخاب نوع نقش (مدیر مدرسه خاص / مدیر مؤسسه آموزشی خاص) |
| `DocumentUpload` | TouchableOpacity + Text | بخش بارگذاری فایل، نمایش نام فایل پس از انتخاب |
| `SubmitButton` | TouchableOpacity | دکمه ثبت درخواست |
| `SuccessCard` | View | کارت نمایش موفقیت پس از ارسال |
| `TrackingLink` | TouchableOpacity | لینک به صفحه پیگیری درخواست |
| `BackButton` | TouchableOpacity | بازگشت به صفحه قبل |

---

## ۳. منطق فرانت‌اند (React Native + Expo)

```tsx
// screens/UploadManagementDocumentScreen.tsx
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Alert, ActivityIndicator, ScrollView } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { api } from '../services/api';

type RoleType = 'school_admin' | 'institute_admin';

export default function UploadManagementDocumentScreen({ navigation, route }) {
  const [roleType, setRoleType] = useState<RoleType>('school_admin');
  const [document, setDocument] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [trackingId, setTrackingId] = useState('');

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/jpeg', 'image/png'],
        copyToCacheDirectory: true,
      });
      if (result.assets && result.assets.length > 0) {
        setDocument(result.assets[0]);
      }
    } catch (err) {
      Alert.alert('خطا', 'انتخاب فایل امکان‌پذیر نیست');
    }
  };

  const submitRequest = async () => {
    if (!document) {
      Alert.alert('خطا', 'لطفاً فایل نامه معرفی را انتخاب کنید.');
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('roleType', roleType);
    formData.append('document', {
      uri: document.uri,
      name: document.name,
      type: document.mimeType || 'application/octet-stream',
    } as any);
    try {
      const res = await api.post('/user/management-role-requests', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setTrackingId(res.data.trackingId);
      setSubmitted(true);
    } catch (err) {
      Alert.alert('خطا', 'ثبت درخواست انجام نشد. لطفاً دوباره تلاش کنید.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <ScrollView style={{ padding: 20, backgroundColor: '#fff', flex: 1 }}>
        <View style={{ alignItems: 'center', marginTop: 50 }}>
          <Text style={{ fontSize: 28, color: '#4caf50', marginBottom: 16 }}>✅ درخواست ثبت شد</Text>
          <Text style={{ fontSize: 16, marginBottom: 8 }}>شماره پیگیری: {trackingId}</Text>
          <Text style={{ textAlign: 'center', marginVertical: 16 }}>وضعیت: در انتظار بررسی (حداکثر ۲ روز کاری)</Text>
          <TouchableOpacity
            onPress={() => navigation.navigate('RequestStatus', { requestId: trackingId })}
            style={{ backgroundColor: '#0066cc', padding: 12, borderRadius: 8, width: '80%', alignItems: 'center', marginBottom: 12 }}
          >
            <Text style={{ color: '#fff', fontWeight: 'bold' }}>مشاهده وضعیت درخواست</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 12 }}>
            <Text style={{ color: '#888' }}>بازگشت</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={{ padding: 20, backgroundColor: '#fff', flex: 1 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginVertical: 20 }}>بارگذاری مدارک برای تأیید نقش مدیریت</Text>
      
      <Text style={{ marginBottom: 8 }}>نوع نقش درخواستی:</Text>
      <View style={{ flexDirection: 'row', marginBottom: 20 }}>
        <TouchableOpacity onPress={() => setRoleType('school_admin')} style={{ flexDirection: 'row', alignItems: 'center', marginRight: 20 }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: roleType === 'school_admin' ? '#0066cc' : '#fff' }} />
          <Text>مدیر مدرسه خاص</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setRoleType('institute_admin')} style={{ flexDirection: 'row', alignItems: 'center' }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: roleType === 'institute_admin' ? '#0066cc' : '#fff' }} />
          <Text>مدیر مؤسسه آموزشی خاص</Text>
        </TouchableOpacity>
      </View>

      <View style={{ borderWidth: 1, borderColor: '#ccc', borderRadius: 12, padding: 16, marginBottom: 24 }}>
        <Text style={{ fontWeight: 'bold', marginBottom: 8 }}>📄 نامه معرفی (با سربرگ و مهر)</Text>
        <Text style={{ marginBottom: 12, fontSize: 12, color: '#555' }}>
          نامه باید شامل اطلاعات زیر باشد:
          • نام و نام خانوادگی نماینده/مدیر
          • شماره همراه
          • کد ملی
        </Text>
        <TouchableOpacity onPress={pickDocument} style={{ backgroundColor: '#0066cc', padding: 10, borderRadius: 8, alignItems: 'center', marginBottom: 8 }}>
          <Text style={{ color: '#fff' }}>انتخاب فایل</Text>
        </TouchableOpacity>
        {document && <Text style={{ fontSize: 12, color: '#2e7d32' }}>✅ فایل انتخاب شد: {document.name}</Text>}
      </View>

      <TouchableOpacity onPress={submitRequest} disabled={loading} style={{ backgroundColor: '#4caf50', padding: 14, borderRadius: 8, alignItems: 'center', marginBottom: 16 }}>
        <Text style={{ color: '#fff', fontWeight: 'bold' }}>{loading ? 'در حال ارسال...' : 'ثبت درخواست'}</Text>
      </TouchableOpacity>

      <Text style={{ fontSize: 12, color: '#888', textAlign: 'center', marginBottom: 20 }}>
        ⚠️ مدارک ارسالی توسط پشتیبان سامانه بررسی می‌شود. در صورت تأیید، نقش مدیریت به حساب شما اضافه می‌شود.
      </Text>

      <TouchableOpacity onPress={() => navigation.goBack()} style={{ alignItems: 'center', padding: 10 }}>
        <Text style={{ color: '#888' }}>بازگشت</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}
```

---

## ۴. منطق بک‌اند (FastAPI + PostgreSQL)

### ۴.۱. مدل داده (جدول درخواست‌های نقش مدیریت)

```sql
CREATE TABLE management_role_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_type VARCHAR(50) NOT NULL, -- 'school_admin' or 'institute_admin'
    document_path TEXT NOT NULL, -- مسیر فایل ذخیره شده
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    tracking_id VARCHAR(20) UNIQUE NOT NULL,
    reviewed_by UUID REFERENCES users(id), -- پشتیبان سامانه
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

### ۴.۲. API ثبت درخواست

#### `POST /user/management-role-requests`

- **نیاز به توکن سطح ۱ (احراز هویت شده)**
- **بدن:** multipart/form-data شامل:
  - `roleType`: `school_admin` یا `institute_admin`
  - `document`: فایل (PDF یا تصویر)
- **مراحل پردازش:**
  1. استخراج `userId` از توکن.
  2. بررسی اینکه آیا کاربر قبلاً درخواست pending برای همان roleType دارد؟ اگر بله، پاسخ `409`.
  3. اعتبارسنجی فایل (نوع، حداکثر حجم ۵ مگابایت، اسکن آنتی‌ویروس).
  4. ذخیره فایل در فضای امن (S3 یا سیستم فایل) با نام یکتا.
  5. ایجاد رکورد در `management_role_requests` با `status='pending'` و تولید `tracking_id` یکتا (مثلاً `REQ-{timestamp}-{random}`).
  6. ارسال اعلان به پشتیبان سامانه (از طریق ایمیل یا پنل اعلان‌ها).
  7. پاسخ: `{ message: "request submitted", trackingId: "..." }`

### ۴.۳. API برای پشتیبان سامانه (مشاهده و تأیید درخواست‌ها)

#### `GET /admin/management-role-requests?status=pending`
- نیاز به توکن مدیر پشتیبان سامانه.
- برگرداندن لیست درخواست‌ها با اطلاعات کاربر و لینک فایل.

#### `POST /admin/management-role-requests/{requestId}/approve`
- **بدن:** (اختیاری) `{ notes: "تأیید شد" }`
- **مراحل:**
  1. دریافت رکورد درخواست.
  2. بررسی اینکه کاربر (صاحب درخواست) قبلاً اکانت با نقش اصلی مربوطه دارد یا خیر. اگر ندارد، ابتدا اکانت ایجاد می‌شود (با نقش اصلی `school_admin` یا `institute_admin`).
  3. اضافه کردن نقش تابعه `school_admin_of` یا `institute_admin_of` به اکانت مربوطه (با context_id مدرسه یا مؤسسه). در این مرحله، `context_id` مشخص نیست؛ بنابراین یا از کاربر خواسته می‌شود نام مدرسه/مؤسسه را وارد کند، یا از مدارک استخراج می‌شود. برای سادگی، فرض می‌کنیم پس از تأیید، مدیر پشتیبان مدرسه/مؤسسه را به صورت دستی انتخاب می‌کند (در پنل مدیریت).
  4. به‌روزرسانی وضعیت درخواست به `approved`.
  5. ارسال اعلان به کاربر.

#### `POST /admin/management-role-requests/{requestId}/reject`
- **بدن:** `{ reason: "دلیل رد" }`
- به‌روزرسانی وضعیت و ذکر دلیل.

---

## ۵. ملاحظات امنیتی

| تهدید | راهکار |
|--------|--------|
| **بارگذاری فایل مخرب** | محدودیت نوع فایل (PDF, JPG, PNG)، اسکن آنتی‌ویروس، حداکثر حجم ۵ مگابایت |
| **دسترسی غیرمجاز به API** | نیاز به توکن سطح ۱ و بررسی مالکیت کاربر برای درخواست‌های شخصی |
| **جعل درخواست برای دیگران** | API از توکن userId استفاده می‌کند، کاربر فقط برای خودش می‌تواند درخواست دهد |
| **تعدد درخواست‌های pending** | جلوگیری از درخواست تکراری برای همان نوع نقش (بررسی در سرور) |
| **ذخیره امن فایل‌ها** | ذخیره در دایرکتوری خارج از public با دسترسی محدود، نام فایل تغییر یافته (UUID) |

---

## ۶. وضعیت درخواست و پیگیری

کاربر می‌تواند با استفاده از `trackingId` (در صفحه پیگیری درخواست‌ها) وضعیت را مشاهده کند. همچنین در پنل کاربری، لیست درخواست‌های قبلی قابل مشاهده است.

**صفحه پیگیری درخواست‌ها** (ساده):
- ورودی شماره پیگیری
- نمایش وضعیت (در انتظار، تأیید شده، رد شده به همراه دلیل)

---

## ۷. خروجی نهایی

این صفحه تمام نیازهای شما را پوشش می‌دهد:
- انتخاب نوع نقش (مدیر مدرسه خاص / مدیر مؤسسه آموزشی خاص)
- بارگذاری نامه معرفی با سربرگ و مهر
- ذخیره درخواست و تولید شماره پیگیری
- بررسی توسط پشتیبان سامانه
- امکان پیگیری وضعیت

