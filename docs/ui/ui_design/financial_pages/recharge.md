# 📄 صفحه ۲: خرید شارژ برای کاربر (Credit Top-Up)

این صفحه به کاربر اجازه می‌دهد کیف پول خود را افزایش دهد. کاربر از بین مبالغ پیشنهادی سامانه انتخاب می‌کند (یا مبلغ دلخواه وارد می‌کند)، درگاه پرداخت را انتخاب کرده و پرداخت را انجام می‌دهد.

## ۲.۱ رابط کاربری (UI)

```
┌─────────────────────────────────────────────────────────────┐
│                    خرید شارژ (کیف پول)                     │
├─────────────────────────────────────────────────────────────┤
│ موجودی فعلی شما: ۲۵,۰۰۰ تومان                              │
│                                                             │
│ مبلغ شارژ (تومان):                                        │
│ ○ ۱۰,۰۰۰    ○ ۵۰,۰۰۰    ○ ۱۰۰,۰۰۰                         │
│ ○ ۲۰۰,۰۰۰   ○ ۵۰۰,۰۰۰                                      │
│                                                             │
│ (سایر مبالغ: [___________])                                │
│                                                             │
│ انتخاب درگاه پرداخت:                                       │
│ ○ زرین‌پال    ○ Pay.ir    ○ زرین‌کارت                    │
│                                                             │
│ [پرداخت و شارژ]                                            │
└─────────────────────────────────────────────────────────────┘
```

### پس از پرداخت موفق

```
┌─────────────────────────────────────────────────────────────┐
│                      ✅ پرداخت موفق                         │
├─────────────────────────────────────────────────────────────┤
│ مبلغ ۱۰۰,۰۰۰ تومان با موفقیت به کیف پول شما اضافه شد.     │
│ موجودی جدید: ۱۲۵,۰۰۰ تومان                                 │
│ شماره تراکنش: TRX-123457                                   │
│                                                             │
│ [بازگشت به داشبورد]                                        │
└─────────────────────────────────────────────────────────────┘
```

## ۲.۲ کامپوننت‌ها

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `WalletBalance` | متن | نمایش موجودی فعلی کیف پول کاربر (دریافت از API). |
| `AmountSelector` | RadioGroup + TextInput | انتخاب مبلغ از پیشنهادها (۱۰,۰۰۰، ۵۰,۰۰۰، ...) یا وارد کردن دستی. اعتبارسنجی (عدد مثبت، حداکثر سقف معین). |
| `GatewaySelector` | RadioGroup | انتخاب درگاه پرداخت. |
| `PaymentButton` | TouchableOpacity | شروع پرداخت. |
| `SuccessCard` | View | نمایش اطلاعات پس از موفقیت. |

## ۲.۳ منطق فرانت‌اند

```tsx
// screens/CreditPurchaseScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, TextInput, Alert, ActivityIndicator } from 'react-native';
import { api } from '../services/api';
import { usePayment } from '../hooks/usePayment';

export default function CreditPurchaseScreen({ navigation }) {
  const [balance, setBalance] = useState(0);
  const [amount, setAmount] = useState(0);
  const [customAmount, setCustomAmount] = useState('');
  const [selectedGateway, setSelectedGateway] = useState('zarinpal');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  const suggestedAmounts = [10000, 50000, 100000, 200000, 500000];

  useEffect(() => {
    fetchBalance();
  }, []);

  const fetchBalance = async () => {
    try {
      const res = await api.get('/wallet/balance');
      setBalance(res.data.balance);
    } catch (err) {
      Alert.alert('خطا', 'دریافت موجودی ممکن نیست');
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    let finalAmount = amount;
    if (customAmount) {
      finalAmount = parseInt(customAmount);
      if (isNaN(finalAmount) || finalAmount <= 0) {
        Alert.alert('خطا', 'مبلغ معتبر وارد کنید');
        return;
      }
      if (finalAmount < 1000) {
        Alert.alert('خطا', 'حداقل مبلغ ۱,۰۰۰ تومان است');
        return;
      }
    }
    if (finalAmount <= 0) {
      Alert.alert('خطا', 'لطفاً مبلغی را انتخاب کنید');
      return;
    }
    setProcessing(true);
    try {
      const res = await api.post('/credit/purchase', {
        amount: finalAmount,
        gateway: selectedGateway,
      });
      const { paymentUrl, transactionId } = res.data;
      const result = await usePayment(paymentUrl);
      if (result.success) {
        await api.post('/credit/verify', { transactionId, gateway: selectedGateway });
        Alert.alert('موفق', 'شارژ با موفقیت اضافه شد.');
        navigation.replace('CreditSuccess', { transactionId, addedAmount: finalAmount });
      } else {
        Alert.alert('خطا', 'پرداخت ناموفق بود');
      }
    } catch (err) {
      Alert.alert('خطا', 'شروع پرداخت ممکن نیست');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) return <ActivityIndicator size="large" />;

  return (
    <View style={{ padding: 20, flex: 1 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 16 }}>خرید شارژ</Text>
      <Text style={{ marginBottom: 20 }}>موجودی فعلی: {balance.toLocaleString()} تومان</Text>
      <Text style={{ fontWeight: 'bold' }}>مبلغ شارژ (تومان):</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginVertical: 12 }}>
        {suggestedAmounts.map(amt => (
          <TouchableOpacity key={amt} onPress={() => { setAmount(amt); setCustomAmount(''); }} style={{ margin: 4, padding: 8, backgroundColor: amount === amt ? '#0066cc' : '#ddd', borderRadius: 8 }}>
            <Text style={{ color: amount === amt ? '#fff' : '#000' }}>{amt.toLocaleString()}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <TextInput
        placeholder="سایر مبالغ (تومان)"
        value={customAmount}
        onChangeText={(v) => { setCustomAmount(v); setAmount(0); }}
        keyboardType="number-pad"
        style={{ borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12, marginVertical: 8 }}
      />
      <Text style={{ marginTop: 16, fontWeight: 'bold' }}>انتخاب درگاه پرداخت:</Text>
      {['zarinpal', 'payir', 'zarinCard'].map(g => (
        <TouchableOpacity key={g} onPress={() => setSelectedGateway(g)} style={{ flexDirection: 'row', alignItems: 'center', marginVertical: 4 }}>
          <View style={{ width: 20, height: 20, borderRadius: 10, borderWidth: 1, borderColor: '#0066cc', marginRight: 8, backgroundColor: selectedGateway === g ? '#0066cc' : '#fff' }} />
          <Text>{g === 'zarinpal' ? 'زرین‌پال' : g === 'payir' ? 'Pay.ir' : 'زرین‌کارت'}</Text>
        </TouchableOpacity>
      ))}
      <TouchableOpacity onPress={handlePayment} disabled={processing} style={{ backgroundColor: '#4caf50', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 24 }}>
        <Text style={{ color: '#fff', fontWeight: 'bold' }}>{processing ? 'در حال اتصال...' : 'پرداخت و شارژ'}</Text>
      </TouchableOpacity>
    </View>
  );
}
```

## ۲.۴ منطق بک‌اند

### API `GET /wallet/balance` (نیاز به توکن سطح ۱)
- استخراج `userId` از توکن.
- جستجو یا ایجاد `wallet` برای کاربر (اگر وجود نداشت، با موجودی صفر ایجاد شود).
- پاسخ: `{ balance: number }`

### API `POST /credit/purchase` (نیاز به توکن سطح ۱)
- **بدن:** `{ amount, gateway }`
- **مراحل:**
  1. اعتبارسنجی مبلغ (بین ۱,۰۰۰ تا ۵,۰۰۰,۰۰۰ تومان – سقف قابل تنظیم).
  2. ایجاد تراکنش با `user_id`، `amount`، `type='credit_purchase'`، `status='pending'`.
  3. دریافت `paymentUrl` از درگاه.
  4. ذخیره `gateway_transaction_id`.
  5. پاسخ: `{ paymentUrl, transactionId }`

### API `POST /credit/verify` (نیاز به توکن سطح ۱)
- **بدن:** `{ transactionId, gateway }`
- **مراحل:**
  1. دریافت تراکنش.
  2. بررسی پرداخت از درگاه.
  3. در صورت موفقیت:
     - به‌روزرسانی `status='success'`.
     - افزایش موجودی کیف پول کاربر به میزان `amount`.
     - به‌روزرسانی `updated_at`.
     - ارسال اعلان به کاربر.
  4. پاسخ: `{ success: true }`

---
