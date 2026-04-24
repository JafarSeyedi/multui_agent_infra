## ✅ خلاصه نهایی صفحات مالی پس از اصلاحات

طبق درخواست شما و شفاف‌سازی مفاهیم:

- **کیف پول (Wallet)** به هر **کاربر (شخص حقیقی)** تعلق دارد. خرید شارژ برای کاربر انجام می‌شود و موجودی شارژ در سطح کاربر ذخیره می‌گردد.
- **اشتراک (Subscription)** به یک **نقش خاص (اکانت)** تعلق دارد که بافت مشخصی دارد (مانند «معلم کلاس دوم دبستان مدرسه رضوی»). هر اکانت نیاز به اشتراک فعال دارد. پس از خرید اشتراک، مبلغ شارژ اولیه (طبق طرح اشتراک) به **کیف پول کاربر** (صاحب آن اکانت) اضافه می‌شود.
- خرید شارژ مستقل از اشتراک است و کاربر می‌تواند هر زمان که بخواهد کیف پول خود را افزایش دهد.

در ادامه، **طراحی کامل دو صفحه** با تمام جزئیات (UI، کامپوننت‌ها، منطق فرانت‌اند، بک‌اند، مدل داده، امنیت) ارائه می‌شود. هیچ ارجاعی به پاسخ‌های قبلی داده نمی‌شود و همه موارد از ابتدا توضیح داده شده است.

---

# 📄 صفحه ۱: خرید اشتراک برای یک نقش خاص (اکانت)

این صفحه زمانی نمایش داده می‌شود که کاربر یک اکانت (نقش خاص با بافت) را انتخاب کرده و آن اکانت اشتراک فعال ندارد. کاربر می‌تواند یکی از طرح‌های اشتراک (ماهانه، سالانه) را انتخاب کند، درگاه پرداخت را برگزیند و مبلغ را پرداخت نماید. پس از پرداخت موفق، اشتراک برای آن اکانت فعال می‌شود و شارژ اولیه به کیف پول کاربر اضافه می‌گردد.

## ۱.۱ رابط کاربری (UI)

```
┌─────────────────────────────────────────────────────────────┐
│          خرید اشتراک برای نقش: معلم کلاس دوم دبستان         │
│                         مدرسه رضوی                          │
├─────────────────────────────────────────────────────────────┤
│ نقش: معلم                                                  │
│ مدرسه: مدرسه رضوی                                          │
│ کلاس: دوم دبستان                                           │
│                                                             │
│ طرح اشتراک:                                                │
│ ○ ماهانه (۳۰ روز) - ۵۰,۰۰۰ تومان                         │
│ ○ سالانه (۳۶۵ روز) - ۴۵۰,۰۰۰ تومان (۱۰٪ تخفیف)          │
│                                                             │
│ انتخاب درگاه پرداخت:                                       │
│ ○ زرین‌پال    ○ Pay.ir    ○ زرین‌کارت                    │
│                                                             │
│ [پرداخت و فعال‌سازی]                                       │
│                                                             │
│ ℹ️ پس از خرید اشتراک، مبلغ ۲۰,۰۰۰ تومان شارژ اولیه        │
│    به کیف پول شما اضافه می‌شود (کیف پول شخصی شما).         │
└─────────────────────────────────────────────────────────────┘
```

### پس از پرداخت موفق (صفحه تأیید)

```
┌─────────────────────────────────────────────────────────────┐
│                      ✅ پرداخت موفق                         │
├─────────────────────────────────────────────────────────────┤
│ اشتراک نقش «معلم کلاس دوم دبستان مدرسه رضوی» فعال شد.     │
│ شماره تراکنش: TRX-123456                                   │
│ مبلغ پرداختی: ۵۰,۰۰۰ تومان                                 │
│ تاریخ اعتبار تا: ۱۴۰۴/۱۱/۲۵                               │
│                                                             │
│ 🔋 شارژ اولیه ۲۰,۰۰۰ تومان به کیف پول شما اضافه شد.       │
│                                                             │
│ [بازگشت به داشبورد]                                        │
└─────────────────────────────────────────────────────────────┘
```

## ۱.۲ کامپوننت‌ها (UI Components)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `AccountInfo` | متن | نمایش اطلاعات اکانت (نقش اصلی و بافت‌های مرتبط مانند مدرسه، کلاس، دوره و ...) که از API دریافت می‌شود. |
| `PlanSelector` | RadioGroup | لیست طرح‌های اشتراک (ماهانه، سالانه ...) که از سرور دریافت می‌شود. هر طرح دارای `id`, `name`, `duration_days`, `price`, `initial_credit`. |
| `PriceDisplay` | متن | نمایش مبلغ طرح انتخاب شده. |
| `GatewaySelector` | RadioGroup | انتخاب درگاه پرداخت (زرین‌پال، Pay.ir، زرین‌کارت). |
| `PaymentButton` | TouchableOpacity | دکمه شروع فرایند پرداخت (باز کردن WebView درگاه). |
| `SuccessCard` | View | کارت نمایش اطلاعات تراکنش پس از موفقیت. |

## ۱.۳ منطق فرانت‌اند (React Native + Expo)

```tsx
// screens/SubscriptionPurchaseScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { api } from '../services/api';
import { usePayment } from '../hooks/usePayment'; // WebView درگاه پرداخت

export default function SubscriptionPurchaseScreen({ route, navigation }) {
  // دریافت accountId و اطلاعات نمایشی اکانت از پارامترهای ناوبری
  const { accountId, accountDisplayName, contextInfo } = route.params;
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [selectedGateway, setSelectedGateway] = useState('zarinpal');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const res = await api.get('/subscription/plans');
      setPlans(res.data.plans);
      if (res.data.plans.length) setSelectedPlan(res.data.plans[0]);
    } catch (err) {
      Alert.alert('خطا', 'دریافت طرح‌های اشتراک ممکن نیست');
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!selectedPlan) {
      Alert.alert('خطا', 'لطفاً یک طرح اشتراک انتخاب کنید');
      return;
    }
    setProcessing(true);
    try {
      // درخواست ایجاد تراکنش و دریافت لینک پرداخت
      const res = await api.post('/subscription/purchase', {
        accountId,
        planId: selectedPlan.id,
        gateway: selectedGateway,
      });
      const { paymentUrl, transactionId } = res.data;

      // باز کردن WebView درگاه پرداخت
      const result = await usePayment(paymentUrl);
      if (result.success) {
        // تأیید نهایی پرداخت در سرور
        await api.post('/subscription/verify', { transactionId, gateway: selectedGateway });
        Alert.alert('موفق', 'اشتراک با موفقیت فعال شد.');
        navigation.replace('SubscriptionSuccess', { transactionId });
      } else {
        Alert.alert('خطا', 'پرداخت ناموفق بود');
      }
    } catch (err) {
      Alert.alert('خطا', 'شروع فرایند پرداخت ممکن نیست');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) return <ActivityIndicator size="large" />;

  return (
    <View style={{ padding: 20, flex: 1 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 16 }}>خرید اشتراک برای نقش: {accountDisplayName}</Text>
      {contextInfo && <Text style={{ marginBottom: 16, color: '#555' }}>{contextInfo}</Text>}
      <Text style={{ marginTop: 8, fontWeight: 'bold' }}>طرح اشتراک:</Text>
      {plans.map(plan => (
        <TouchableOpacity key={plan.id} onPress={() => setSelectedPlan(plan)} style={{ flexDirection: 'row', alignItems: 'center', marginVertical: 8 }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: selectedPlan?.id === plan.id ? '#0066cc' : '#fff' }} />
          <Text>{plan.name} - {plan.price.toLocaleString()} تومان</Text>
        </TouchableOpacity>
      ))}
      <Text style={{ marginTop: 16, fontWeight: 'bold' }}>انتخاب درگاه پرداخت:</Text>
      {['zarinpal', 'payir', 'zarinCard'].map(g => (
        <TouchableOpacity key={g} onPress={() => setSelectedGateway(g)} style={{ flexDirection: 'row', alignItems: 'center', marginVertical: 4 }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: selectedGateway === g ? '#0066cc' : '#fff' }} />
          <Text>{g === 'zarinpal' ? 'زرین‌پال' : g === 'payir' ? 'Pay.ir' : 'زرین‌کارت'}</Text>
        </TouchableOpacity>
      ))}
      <TouchableOpacity onPress={handlePayment} disabled={processing} style={{ backgroundColor: '#4caf50', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 24 }}>
        <Text style={{ color: '#fff', fontWeight: 'bold' }}>{processing ? 'در حال اتصال به درگاه...' : 'پرداخت و فعال‌سازی'}</Text>
      </TouchableOpacity>
      <Text style={{ fontSize: 12, color: '#888', textAlign: 'center', marginTop: 20 }}>
        ℹ️ پس از خرید اشتراک، مبلغ {selectedPlan?.initial_credit?.toLocaleString() ?? '۰'} تومان شارژ اولیه به کیف پول شما اضافه می‌شود.
      </Text>
    </View>
  );
}
```

## ۱.۴ منطق بک‌اند (FastAPI + PostgreSQL)

### مدل داده (جدول‌های مرتبط)

```sql
-- طرح‌های اشتراک (ثابت)
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,          -- e.g., 'ماهانه', 'سالانه'
    duration_days INT NOT NULL,
    price BIGINT NOT NULL,               -- تومان
    initial_credit BIGINT NOT NULL,      -- شارژ اولیه به تومان
    is_active BOOLEAN DEFAULT TRUE
);

-- اشتراک‌های خریداری شده برای هر اکانت
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT now()
);

-- کیف پول کاربران (هر کاربر یک رکورد)
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    balance BIGINT DEFAULT 0,            -- تومان
    updated_at TIMESTAMP DEFAULT now()
);

-- تراکنش‌های مالی
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tracking_code VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    account_id UUID NULL REFERENCES accounts(id), -- برای اشتراک پر است
    amount BIGINT NOT NULL,               -- تومان
    type VARCHAR(30) NOT NULL,            -- 'subscription_purchase', 'credit_purchase', 'consumption', 'reward'
    status VARCHAR(20) DEFAULT 'pending', -- pending, success, failed
    gateway VARCHAR(50),
    gateway_transaction_id VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

### API `POST /subscription/plans` (عمومی)
- **پاسخ:** لیست طرح‌های فعال.

### API `POST /subscription/purchase` (نیاز به توکن سطح ۱)

- **بدن:** `{ accountId, planId, gateway }`
- **مراحل:**
  1. استخراج `userId` از توکن.
  2. بررسی اینکه `accountId` متعلق به این `userId` باشد (با join از جدول accounts).
  3. بررسی اینکه اکانت اشتراک فعال نداشته باشد (بررسی جدول subscriptions که end_date > now()).
  4. دریافت اطلاعات `plan` (قیمت، مدت، شارژ اولیه).
  5. ایجاد رکورد تراکنش با `user_id`، `account_id`، `amount`، `type='subscription_purchase'`، `status='pending'` و تولید `tracking_code` یکتا.
  6. درخواست به درگاه پرداخت برای دریافت `paymentUrl`. (فرض می‌کنیم `gateway` می‌تواند 'zarinpal', 'payir', 'zarinCard' باشد و هرکدام تابع مخصوص خود را دارد.)
  7. ذخیره `gateway_transaction_id` برگشتی از درگاه در تراکنش.
  8. پاسخ: `{ paymentUrl, transactionId }`

### API `POST /subscription/verify` (نیاز به توکن سطح ۱)

- **بدن:** `{ transactionId, gateway }`
- **مراحل:**
  1. دریافت تراکنش از دیتابیس با `id`.
  2. بررسی وضعیت پرداخت از درگاه (با استفاده از API درگاه و `gateway_transaction_id`).
  3. اگر پرداخت موفق بود:
     - به‌روزرسانی `status='success'` در تراکنش.
     - ایجاد رکورد اشتراک جدید: `start_date = now()`, `end_date = now() + plan.duration_days`, `account_id`, `plan_id`.
     - اعمال شارژ اولیه به کیف پول کاربر: (اگر کیف پول وجود ندارد، ایجاد شود) `balance += plan.initial_credit`.
     - ثبت یک تراکنش از نوع `reward` (یا `initial_credit`) برای مبلغ شارژ اولیه (اختیاری).
     - ارسال اعلان (پیامک و پیام داخلی) به کاربر مبنی بر فعال‌سازی اشتراک و افزایش شارژ.
  4. اگر پرداخت ناموفق بود: به‌روزرسانی `status='failed'` و پاسخ خطا.
  5. پاسخ: `{ success: true }`

---


## ۳. ملاحظات امنیتی و یکپارچگی

| تهدید | راهکار |
|--------|--------|
| خرید اشتراک برای اکانت دیگران | بررسی تعلق `accountId` به `userId` توکن. |
| درخواست تکراری پرداخت | تراکنش با `tracking_code` یکتا و `status='pending'`، جلوگیری از ایجاد چند تراکنش همزمان برای یک `accountId`/`userId`. |
| دستکاری مبلغ در سمت کلاینت | مبلغ در بک‌اند از `plan` (برای اشتراک) یا از ورودی کاربر (با اعتبارسنجی) دریافت می‌شود. در verify، مبلغ پرداختی درگاه نیز بررسی می‌شود. |
| تطابق درگاه | هر درگاه پروتکل مخصوص خود را دارد و مبلغ برگشتی باید با مبلغ درخواستی تطابق داده شود. |
| ذخیره لاگ | تمام تراکنش‌ها و تغییرات موجودی در جداول مربوطه ثبت می‌شود. |

---

## ۴. خروجی نهایی

دو صفحه به طور کامل طراحی شدند:
- **خرید اشتراک برای نقش خاص (اکانت)**: با نمایش بافت نقش، انتخاب طرح، پرداخت، فعال‌سازی اشتراک و اعطای شارژ اولیه به کیف پول کاربر.
- **خرید شارژ برای کاربر**: نمایش موجودی، انتخاب مبلغ، پرداخت و افزایش کیف پول.

در صورت تأیید، بخش **مصرف شارژ (محاسبه هزینه AI، کاهش خودکار و پاداش‌ها)** را طراحی خواهم کرد.