## ✅ صفحه ۳: ایجاد اکانت جدید (Create Account)

این صفحه به کاربر (اعم از جدید یا قدیمی) اجازه می‌دهد یک اکانت جدید با **نقش اصلی دلخواه** ایجاد کند. کاربر باید نوع اکانت (دانش‌آموز، معلم، والدین، و غیره) را انتخاب کرده و مدارک و اطلاعات مورد نیاز را ارائه دهد. پس از ارسال درخواست، مدارک توسط مقام مربوطه (مدیر پشتیبان، مدیر مدرسه، و ...) بررسی شده و در صورت تأیید، اکانت جدید با نقش اصلی مشخص شده ایجاد می‌شود.

**نکته:** کاربر می‌تواند چندین اکانت با نقش‌های اصلی متفاوت داشته باشد. این صفحه هم برای کاربران جدید (که اولین اکانت خود را می‌سازند) و هم برای کاربران قدیمی (که اکانت اضافی می‌خواهند) قابل استفاده است.

---

### ۱. هدف صفحه
امکان درخواست ایجاد یک اکانت جدید با یک **نقش اصلی** (نوع اکانت) مشخص، همراه با ارائه مدارک و اطلاعات مورد نیاز برای تأیید آن نقش.

---

### ۲. اجزای صفحه (کامپوننت‌ها)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `Title` | متن | «ایجاد اکانت جدید – هوشیاد» |
| `AccountTypeSelector` | گروه دکمه رادیویی یا کامبوی کشویی | لیست انواع اکانت‌های موجود (نقش اصلی): دانش‌آموز، معلم، والدین، مدیر مدرسه، مدیر موسسه آموزشی، معلم موسسه آموزشی، معلم آزاد، معلم پشتیبان مرکزی، مدیر پشتیبان سامانه |
| `DynamicForm` | فرم پویا | بر اساس نوع انتخاب شده، فیلدهای اختصاصی (مدارک، اطلاعات تکمیلی) نمایش داده می‌شود. |
| `DocumentUpload` | کامپوننت بارگذاری فایل | امکان بارگذاری تصاویر، PDF، فیلم (با محدودیت حجم و نوع) |
| `SubmitButton` | دکمه | ارسال درخواست ایجاد اکانت |
| `StatusMessage` | متن | نمایش وضعیت ارسال (در انتظار، موفق، خطا) |
| `BackLink` | لینک | بازگشت به صفحه قبل (مدیریت اکانت‌ها یا داشبورد) |
| `InfoText` | متن | توضیح کوتاه درباره فرآیند تأیید (ممکن است چند روز طول بکشد) |

---

### ۳. منطق فرانت‌اند (React Native + Expo)

```tsx
// screens/CreateAccountScreen.tsx
import { useState } from 'react';
import { View, Text, Button, RadioButton, TextInput, Alert, ScrollView } from 'react-native';
import { api } from '../services/api';
import DocumentPicker from 'react-native-document-picker';

type AccountType = 
  | 'student' 
  | 'teacher' 
  | 'parent' 
  | 'school_admin' 
  | 'institute_admin' 
  | 'institute_teacher' 
  | 'free_teacher'
  | 'central_support_teacher'
  | 'system_admin'; // موارد اضافی

const accountTypeLabels: Record<AccountType, string> = {
  student: 'دانش‌آموز',
  teacher: 'معلم',
  parent: 'والدین',
  school_admin: 'مدیر مدرسه',
  institute_admin: 'مدیر مؤسسه آموزشی',
  institute_teacher: 'معلم مؤسسه آموزشی',
  free_teacher: 'معلم آزاد',
  central_support_teacher: 'معلم پشتیبان مرکزی',
  system_admin: 'مدیر پشتیبان سامانه'
};

export default function CreateAccountScreen({ navigation, route }) {
  const [selectedType, setSelectedType] = useState<AccountType | null>(null);
  const [extraInfo, setExtraInfo] = useState({});
  const [documents, setDocuments] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  const handleTypeChange = (type: AccountType) => {
    setSelectedType(type);
    setExtraInfo({});
    setDocuments({});
  };

  const uploadDocument = async (key: string) => {
    try {
      const res = await DocumentPicker.pick({ type: [DocumentPicker.types.images, DocumentPicker.types.pdf] });
      setDocuments({ ...documents, [key]: res[0] });
    } catch (err) {
      console.log(err);
    }
  };

  const renderDynamicForm = () => {
    if (!selectedType) return null;
    switch (selectedType) {
      case 'student':
        return (
          <>
            <Text>پایه تحصیلی: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, grade: v})} /></Text>
            <Text>نام مدرسه (اختیاری): <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, schoolName: v})} /></Text>
            <Button title="بارگذاری کارت ملی دانش‌آموز" onPress={() => uploadDocument('studentCard')} />
            {documents.studentCard && <Text>✅ بارگذاری شد</Text>}
            <Button title="بارگذاری عکس پرسنلی" onPress={() => uploadDocument('profilePhoto')} />
          </>
        );
      case 'teacher':
        return (
          <>
            <Text>مدرک تحصیلی: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, degree: v})} /></Text>
            <Text>سابقه تدریس (سال): <TextInput keyboardType="number-pad" onChangeText={(v) => setExtraInfo({...extraInfo, experienceYears: v})} /></Text>
            <Button title="بارگذاری کارت ملی" onPress={() => uploadDocument('nationalIdCard')} />
            <Button title="بارگذاری مدرک تحصیلی" onPress={() => uploadDocument('degreeDoc')} />
            <Button title="بارگذاری رزومه" onPress={() => uploadDocument('resume')} />
          </>
        );
      case 'parent':
        return (
          <>
            <Text>کد ملی دانش‌آموز (فرزند): <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, childNationalId: v})} /></Text>
            <Button title="بارگذاری کارت ملی والدین" onPress={() => uploadDocument('parentCard')} />
            <Button title="بارگذاری شناسنامه (صفحات اول و دوم)" onPress={() => uploadDocument('birthCertificate')} />
          </>
        );
      case 'school_admin':
        return (
          <>
            <Text>نام مدرسه: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, schoolName: v})} /></Text>
            <Button title="بارگذاری نامه معرفی از مدرسه" onPress={() => uploadDocument('introductionLetter')} />
            <Button title="بارگذاری کارت ملی مدیر" onPress={() => uploadDocument('adminCard')} />
          </>
        );
      case 'institute_admin':
        return (
          <>
            <Text>نام مؤسسه: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, instituteName: v})} /></Text>
            <Button title="بارگذاری مجوز تأسیس مؤسسه" onPress={() => uploadDocument('license')} />
            <Button title="بارگذاری کارت ملی مدیر" onPress={() => uploadDocument('adminCard')} />
          </>
        );
      case 'institute_teacher':
        return (
          <>
            <Text>نام مؤسسه: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, instituteName: v})} /></Text>
            <Button title="بارگذاری کارت ملی" onPress={() => uploadDocument('nationalIdCard')} />
            <Button title="بارگذاری قرارداد با مؤسسه" onPress={() => uploadDocument('contract')} />
          </>
        );
      case 'free_teacher':
        return (
          <>
            <Text>حوزه تدریس: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, subjectArea: v})} /></Text>
            <Button title="بارگذاری کارت ملی" onPress={() => uploadDocument('nationalIdCard')} />
            <Button title="بارگذاری مدارک حرفه‌ای" onPress={() => uploadDocument('professionalDocs')} />
          </>
        );
      case 'central_support_teacher':
        return (
          <>
            <Text>نام و نام خانوادگی: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, fullname: v})} /></Text>
            <Text>سابقه تدریس در سامانه‌های مشابه: <TextInput onChangeText={(v) => setExtraInfo({...extraInfo, similarExperience: v})} /></Text>
            <Button title="بارگذاری رزومه" onPress={() => uploadDocument('resume')} />
            <Text style={{fontSize:12, color:'gray'}}>این نقش فقط توسط مدیر پشتیبان سامانه قابل تأیید است.</Text>
          </>
        );
      case 'system_admin':
        return (
          <Text>ایجاد این نقش فقط توسط مدیر سامانه امکان‌پذیر است. درخواست شما ثبت و بررسی می‌شود.</Text>
        );
      default:
        return null;
    }
  };

  const submitRequest = async () => {
    if (!selectedType) { Alert.alert('لطفاً نوع اکانت را انتخاب کنید'); return; }
    // بررسی مدارک اجباری (بسته به نقش) – در اینجا خلاصه شده
    setIsSubmitting(true);
    setStatus('submitting');
    const formData = new FormData();
    formData.append('accountType', selectedType);
    formData.append('extraInfo', JSON.stringify(extraInfo));
    for (const [key, file] of Object.entries(documents)) {
      formData.append(key, file);
    }
    try {
      await api.post('/accounts/requests', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setStatus('success');
      Alert.alert('درخواست شما ثبت شد. پس از تأیید، اکانت جدید فعال می‌شود.');
      navigation.goBack(); // بازگشت به صفحه قبل
    } catch (err) {
      setStatus('error');
      Alert.alert('خطا در ثبت درخواست. لطفاً دوباره تلاش کنید.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScrollView style={{ padding: 20 }}>
      <Text style={{ fontSize: 24, textAlign: 'center' }}>ایجاد اکانت جدید</Text>
      <Text style={{ marginVertical: 10 }}>نوع اکانت (نقش اصلی) را انتخاب کنید:</Text>
      <RadioButton.Group onValueChange={handleTypeChange} value={selectedType}>
        {Object.entries(accountTypeLabels).map(([value, label]) => (
          <RadioButton.Item key={value} label={label} value={value} />
        ))}
      </RadioButton.Group>

      {renderDynamicForm()}

      <Button title="ارسال درخواست" onPress={submitRequest} disabled={isSubmitting} />
      {status === 'submitting' && <Text>در حال ارسال...</Text>}
    </ScrollView>
  );
}
```

---

### ۴. منطق بک‌اند (FastAPI + PostgreSQL)

#### مدل داده (اضافه شدن به مدل قبلی)

```sql
-- جدول درخواست‌های ایجاد اکانت (همان role_requests می‌تواند باشد با فیلد account_type)
CREATE TABLE account_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    requested_account_type VARCHAR(50) NOT NULL, -- student, teacher, parent, ...
    extra_info JSONB,
    documents JSONB,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- جدول اکانت‌ها (پس از تأیید درخواست، یک رکورد در اینجا ایجاد می‌شود)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_type VARCHAR(50) NOT NULL, -- primary role
    display_name VARCHAR(100), -- نام قابل نمایش برای این اکانت (اختیاری)
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);

-- جدول نقش‌های تابعه (ثانویه) – بعداً
CREATE TABLE account_secondary_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    role_type VARCHAR(50) NOT NULL, -- e.g., 'school_admin_of', 'class_teacher_of', ...
    context_id UUID, -- e.g., school_id, class_id, course_id
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT now()
);
```

#### API: `POST /accounts/requests` (نیاز به توکن سطح ۱)

- **هدر:** `Authorization: Bearer <token>`
- **بدن:** multipart/form-data شامل:
  - `accountType` (رشته از لیست مجاز)
  - `extraInfo` (JSON)
  - فایل‌ها (مطابق با نوع اکانت)
- **مراحل پردازش:**
  1. استخراج `userId` از توکن.
  2. اعتبارسنجی نوع اکانت (فقط مقادیر مجاز).
  3. بررسی اینکه آیا کاربر درخواست pending برای همان نوع اکانت دارد؟ (جلوگیری از درخواست تکراری)
  4. ذخیره فایل‌ها در فضای امن (S3 یا سیستم فایل) با نام یکتا.
  5. ایجاد رکورد در `account_requests` با `status='pending'`.
  6. ارسال اعلان به مدیر مربوطه (بسته به نوع اکانت: برای `school_admin` به مدیر پشتیبان سامانه، برای `teacher` در یک مدرسه خاص به مدیر آن مدرسه و ...). در این مرحله، اطلاع‌رسانی ساده است.
  7. پاسخ: `{ message: "درخواست ثبت شد", requestId }`

#### API برای مدیریت درخواست‌ها (در صفحات بعدی)

- **مدیر پشتیبان سامانه** می‌تواند درخواست‌های انواع خاص را ببیند و تأیید/رد کند.
- **مدیر مدرسه** می‌تواند درخواست‌های معلمی برای مدرسه خود را ببیند.
- پس از تأیید:
  - ایجاد رکورد جدید در `accounts` با `user_id`, `account_type`, `is_default` (اگر اولین اکانت کاربر باشد یا کاربر تعیین کرده باشد).
  - بر اساس `extraInfo`، ممکن است نیاز به ایجاد نقش‌های تابعه نیز باشد (مثلاً اگر کاربر به عنوان معلم کلاس خاص درخواست داده باشد، همزمان نقش معلم کلاس نیز ایجاد می‌شود). اما در این صفحه فقط نقش اصلی ایجاد می‌شود. نقش‌های تابعه در صفحات جداگانه (مدیریت نقش‌ها) اضافه می‌شوند.

---

### ۵. ملاحظات امنیتی

| تهدید | راهکار |
|--------|--------|
| درخواست بدون توکن معتبر | نیاز به توکن سطح ۱ (احراز هویت شده) |
| بارگذاری فایل مخرب | محدودیت نوع و حجم، اسکن آنتی‌ویروس، ذخیره در فضای ایزوله |
| درخواست تکراری برای یک نوع اکانت | بررسی `pending` در دیتابیس |
| دسترسی غیرمجاز به درخواست دیگران | API مدیریت درخواست‌ها بر اساس نقش دسترسی محدود می‌شود |
| جعل نوع اکانت | اعتبارسنجی سرور (فقط مقادیر مجاز) |

---

### ۶. خروجی نهایی (صفحه)

```
ایجاد اکانت جدید – هوشیاد

نوع اکانت (نقش اصلی) را انتخاب کنید:
○ دانش‌آموز
○ معلم
○ والدین
○ مدیر مدرسه
○ مدیر مؤسسه آموزشی
○ معلم مؤسسه آموزشی
○ معلم آزاد
○ معلم پشتیبان مرکزی
○ مدیر پشتیبان سامانه

[پس از انتخاب، فرم پویا نمایش داده می‌شود]

[ارسال درخواست]
```

---

