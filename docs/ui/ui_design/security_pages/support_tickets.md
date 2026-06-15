## ✅ صفحه مدیریت درخواست‌های بارگذاری مدارک برای پشتیبان سامانه (سیستم تیکتینگ)

این صفحه بخشی از **پنل پشتیبانی سامانه** است. پشتیبان سامانه (مدیر پشتیبان سامانه) می‌تواند درخواست‌های بارگذاری مدارک کاربران را که برای تأیید کد ملی یا دریافت نقش‌های مدیریتی (مدیر مدرسه خاص، مدیر مؤسسه خاص) ارسال شده‌اند، به صورت **تیکت** مشاهده کند. برای هر تیکت، پشتیبان می‌تواند:
- مشاهده جزئیات درخواست و فایل‌های بارگذاری شده
- **تأیید** درخواست (با امکان نوشتن یادداشت داخلی)
- **رد** درخواست با ذکر دلیل (که برای کاربر نمایش داده می‌شود)
پس از هر اقدام، **اعلان از طریق پیامک و پیام داخلی** به کاربر ارسال می‌شود. همچنین کاربر می‌تواند در بخش «پیام‌ها» یا «درخواست‌های من» نتیجه را مشاهده کند.

**نکات کلیدی:**
- تیکت‌ها دارای **نوع** (مانند `national_id_verification`, `management_role_request`) هستند.
- وضعیت‌های تیکت: `pending`, `approved`, `rejected`.
- پشتیبان فقط دسترسی به تیکت‌های در انتظار (pending) دارد (یا می‌تواند همه را ببیند با فیلتر).
- پس از تأیید، نقش یا تأیید کد ملی اعمال می‌شود (بسته به نوع تیکت).
- تمام اقدامات ثبت و قابل پیگیری است.

---

## ۱. رابط کاربری (UI)

### صفحه اصلی لیست تیکت‌ها (برای پشتیبان)

```
┌─────────────────────────────────────────────────────────────┐
│              مدیریت درخواست‌های مدارک (تیکت‌ها)            │
├─────────────────────────────────────────────────────────────┤
│ [فیلتر: همه ▼]  [جستجو: ___________]  [تاریخ: از... تا...] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🆔 TKT-12345  |  نوع: تأیید کد ملی                    │ │
│ │ 👤 علی رضایی  |  تاریخ: ۱۴۰۴/۱۰/۲۵  |  وضعیت: ⏳ در انتظار│
│ │ [مشاهده جزئیات]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🆔 TKT-12346  |  نوع: درخواست مدیر مدرسه خاص          │ │
│ │ 👤 سارا موسوی  |  تاریخ: ۱۴۰۴/۱۰/۲۴  |  وضعیت: ⏳ در انتظار│
│ │ [مشاهده جزئیات]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

### صفحه جزئیات تیکت (برای پشتیبان)

```
┌─────────────────────────────────────────────────────────────┐
│              جزئیات تیکت: TKT-12345                         │
├─────────────────────────────────────────────────────────────┤
│ نوع درخواست: تأیید کد ملی                                  │
│ کاربر: علی رضایی (کد ملی: ۱۲۳۴۵۶۷۸۹۰، موبایل: +989123456789)│
│ تاریخ ارسال: ۱۴۰۴/۱۰/۲۵ ۱۰:۳۰                             │
│ وضعیت: در انتظار بررسی                                     │
├─────────────────────────────────────────────────────────────┤
│ مدارک بارگذاری شده:                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📄 کارت ملی: card_123.jpg  [مشاهده]                    │ │
│ │ 📄 شناسنامه صفحه اول: birth1.jpg  [مشاهده]             │ │
│ │ 📄 شناسنامه صفحه دوم: birth2.jpg  [مشاهده]             │ │
│ │ 🎥 فیلم تأیید: video.mp4  [پخش]                        │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ اقدامات:                                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [✅ تأیید درخواست]                                      │ │
│ │ [❌ رد درخواست]                                         │ │
│ │                                                         │ │
│ │ (در صورت رد، دلیل را وارد کنید:)                       │ │
│ │ ┌─────────────────────────────────────────────────────┐ ││
│ │ │ [___________________________________________]       │ ││
│ │ └─────────────────────────────────────────────────────┘ ││
│ │ [ارسال]                                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ تاریخچه اقدامات:                                            │
│ - ایجاد شده توسط کاربر                                     │
└─────────────────────────────────────────────────────────────┘
```

### پس از تأیید/رد (نمایش پیام موفقیت)

```
┌─────────────────────────────────────────────────────────────┐
│ ✅ درخواست با موفقیت تأیید شد.                             │
│ اعلان به کاربر ارسال گردید.                                │
│ [بازگشت به لیست تیکت‌ها]                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## ۲. کامپوننت‌ها (UI Components)

| نام کامپوننت | نوع | توضیح |
|--------------|------|--------|
| `FilterBar` | View | فیلتر بر اساس وضعیت، نوع، تاریخ، جستجو |
| `TicketCard` | TouchableOpacity | نمایش خلاصه تیکت (شناسه، نوع، نام کاربر، تاریخ، وضعیت) |
| `TicketDetailView` | ScrollView | نمایش جزئیات کامل تیکت و مدارک |
| `DocumentViewer` | Modal یا WebView | نمایش تصاویر و پخش ویدیو |
| `ApproveButton` | TouchableOpacity | دکمه تأیید |
| `RejectButton` | TouchableOpacity | دکمه رد (با نمایش TextInput برای دلیل) |
| `HistoryLog` | FlatList | نمایش تاریخچه اقدامات روی تیکت |
| `StatusBadge` | View | نشانگر وضعیت (رنگی) |

---

## ۳. منطق فرانت‌اند (React Native + Expo)

```tsx
// screens/admin/TicketManagementScreen.tsx (لیست تیکت‌ها)
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, TextInput, ActivityIndicator, Alert } from 'react-native';
import { api } from '../../services/api';

export default function TicketManagementScreen({ navigation }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchTickets();
  }, [filter, search]);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const res = await api.get('/admin/tickets', { params: { status: filter, search } });
      setTickets(res.data.tickets);
    } catch (err) {
      Alert.alert('خطا', 'دریافت تیکت‌ها ممکن نیست');
    } finally {
      setLoading(false);
    }
  };

  const renderTicket = ({ item }) => (
    <TouchableOpacity onPress={() => navigation.navigate('TicketDetail', { ticketId: item.id })} style={{ padding: 12, borderBottomWidth: 1, borderColor: '#eee' }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={{ fontWeight: 'bold' }}>{item.trackingId}</Text>
        <Text style={{ color: item.status === 'pending' ? '#f0ad4e' : (item.status === 'approved' ? '#4caf50' : '#f44336') }}>
          {item.status === 'pending' ? 'در انتظار' : item.status === 'approved' ? 'تأیید شده' : 'رد شده'}
        </Text>
      </View>
      <Text>نوع: {item.type === 'national_id' ? 'تأیید کد ملی' : 'درخواست نقش مدیریت'}</Text>
      <Text>کاربر: {item.userFullName}</Text>
      <Text>تاریخ: {item.createdAt}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 16 }}>مدیریت درخواست‌ها (تیکت‌ها)</Text>
      <View style={{ flexDirection: 'row', marginBottom: 12 }}>
        <TextInput placeholder="جستجو..." value={search} onChangeText={setSearch} style={{ flex: 1, borderWidth: 1, borderColor: '#ccc', padding: 8, borderRadius: 8, marginRight: 8 }} />
        <TouchableOpacity onPress={fetchTickets} style={{ backgroundColor: '#0066cc', padding: 8, borderRadius: 8 }}><Text style={{ color: '#fff' }}>جستجو</Text></TouchableOpacity>
      </View>
      <View style={{ flexDirection: 'row', marginBottom: 12 }}>
        {['pending', 'approved', 'rejected', 'all'].map((s) => (
          <TouchableOpacity key={s} onPress={() => setFilter(s)} style={{ marginRight: 10, padding: 6, backgroundColor: filter === s ? '#0066cc' : '#ddd', borderRadius: 8 }}>
            <Text style={{ color: filter === s ? '#fff' : '#000' }}>{s === 'pending' ? 'در انتظار' : s === 'approved' ? 'تأیید شده' : s === 'rejected' ? 'رد شده' : 'همه'}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {loading ? <ActivityIndicator /> : <FlatList data={tickets} renderItem={renderTicket} keyExtractor={item => item.id} />}
    </View>
  );
}
```

```tsx
// screens/admin/TicketDetailScreen.tsx (جزئیات تیکت)
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, TextInput, Alert, ActivityIndicator, Linking } from 'react-native';
import { api } from '../../services/api';

export default function TicketDetailScreen({ route, navigation }) {
  const { ticketId } = route.params;
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchTicket();
  }, []);

  const fetchTicket = async () => {
    try {
      const res = await api.get(`/admin/tickets/${ticketId}`);
      setTicket(res.data);
    } catch (err) {
      Alert.alert('خطا', 'دریافت جزئیات ممکن نیست');
      navigation.goBack();
    } finally {
      setLoading(false);
    }
  };

  const approveTicket = async () => {
    setActionLoading(true);
    try {
      await api.post(`/admin/tickets/${ticketId}/approve`);
      Alert.alert('موفق', 'درخواست تأیید شد. اعلان به کاربر ارسال گردید.');
      navigation.goBack();
    } catch (err) {
      Alert.alert('خطا', 'تأیید انجام نشد');
    } finally {
      setActionLoading(false);
    }
  };

  const rejectTicket = async () => {
    if (!rejectionReason.trim()) {
      Alert.alert('خطا', 'لطفاً دلیل رد را وارد کنید');
      return;
    }
    setActionLoading(true);
    try {
      await api.post(`/admin/tickets/${ticketId}/reject`, { reason: rejectionReason });
      Alert.alert('موفق', 'درخواست رد شد. اعلان به کاربر ارسال گردید.');
      navigation.goBack();
    } catch (err) {
      Alert.alert('خطا', 'رد درخواست انجام نشد');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <ActivityIndicator />;
  if (!ticket) return null;

  return (
    <ScrollView style={{ padding: 16 }}>
      <Text style={{ fontSize: 22, fontWeight: 'bold' }}>جزئیات تیکت: {ticket.trackingId}</Text>
      <Text>نوع: {ticket.type === 'national_id' ? 'تأیید کد ملی' : 'درخواست نقش مدیریت'}</Text>
      <Text>کاربر: {ticket.userFullName} (کد ملی: {ticket.userNationalId})</Text>
      <Text>موبایل: {ticket.userPhone}</Text>
      <Text>تاریخ: {ticket.createdAt}</Text>
      <Text>وضعیت: {ticket.status === 'pending' ? 'در انتظار' : ticket.status === 'approved' ? 'تأیید شده' : 'رد شده'}</Text>

      <Text style={{ marginTop: 16, fontWeight: 'bold' }}>مدارک بارگذاری شده:</Text>
      {ticket.documents.map((doc, idx) => (
        <TouchableOpacity key={idx} onPress={() => Linking.openURL(doc.url)} style={{ marginVertical: 4 }}>
          <Text>📄 {doc.name}</Text>
        </TouchableOpacity>
      ))}

      {ticket.status === 'pending' && (
        <>
          <TouchableOpacity onPress={approveTicket} disabled={actionLoading} style={{ backgroundColor: '#4caf50', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 20 }}>
            <Text style={{ color: '#fff', fontWeight: 'bold' }}>✅ تأیید درخواست</Text>
          </TouchableOpacity>

          <TextInput placeholder="دلیل رد (در صورت رد)" value={rejectionReason} onChangeText={setRejectionReason} multiline style={{ borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12, marginTop: 12, minHeight: 80 }} />
          <TouchableOpacity onPress={rejectTicket} disabled={actionLoading} style={{ backgroundColor: '#f44336', padding: 14, borderRadius: 8, alignItems: 'center', marginTop: 8 }}>
            <Text style={{ color: '#fff', fontWeight: 'bold' }}>❌ رد درخواست</Text>
          </TouchableOpacity>
        </>
      )}

      {ticket.status !== 'pending' && (
        <View style={{ marginTop: 20, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 8 }}>
          <Text style={{ fontWeight: 'bold' }}>تاریخچه:</Text>
          <Text>تأیید/رد توسط: {ticket.reviewerName}</Text>
          <Text>تاریخ: {ticket.reviewedAt}</Text>
          {ticket.rejectionReason && <Text>دلیل رد: {ticket.rejectionReason}</Text>}
        </View>
      )}
    </ScrollView>
  );
}
```

---

## ۴. منطق بک‌اند (FastAPI + PostgreSQL)

### ۴.۱. مدل داده (جدول تیکت‌ها)

```sql
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tracking_id VARCHAR(20) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'national_id_verification', 'management_role_request'
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    documents JSONB, -- لیست فایل‌ها (نام، مسیر)
    extra_data JSONB, -- اطلاعات اضافی (مثل roleType برای درخواست مدیریت)
    rejection_reason TEXT,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);
```

### ۴.۲. APIهای مورد نیاز

#### `GET /admin/tickets` (فقط مدیر پشتیبان سامانه)
- **پارامترها:** `status`, `search`, `from`, `to`
- **پاسخ:** لیست تیکت‌ها با خلاصه اطلاعات کاربر.

#### `GET /admin/tickets/{ticketId}`
- **پاسخ:** جزئیات کامل تیکت، شامل لیست فایل‌ها (با URL قابل دسترسی موقت).

#### `POST /admin/tickets/{ticketId}/approve`
- **بدن:** (اختیاری) `{ notes: string }`
- **عملیات:**
  1. بروزرسانی `status = 'approved'`, `reviewed_by = admin_id`, `reviewed_at = now()`.
  2. بسته به نوع تیکت:
     - `national_id_verification`: بروزرسانی `national_id_verified_at = now()` در جدول `users`.
     - `management_role_request`: ایجاد نقش تابعه (مثلاً `school_admin_of` یا `institute_admin_of`) برای کاربر و در صورت نیاز ایجاد اکانت اصلی (اگر نداشته باشد). همچنین به‌روزرسانی `national_id_verified_at` (چون تأیید مدارک همزمان با تأیید کد ملی است).
  3. ارسال اعلان داخلی (پیام در سامانه) و پیامک به کاربر.
  4. ثبت در لاگ.

#### `POST /admin/tickets/{ticketId}/reject`
- **بدن:** `{ reason: string }`
- **عملیات:** بروزرسانی وضعیت به `rejected`, ذکر دلیل، ارسال اعلان به کاربر.

---

## ۵. ارسال اعلان به کاربر (پیامک + پیام داخلی)

### پیامک (از طریق سرویس SMS)
- متن برای تأیید: «درخواست شما با شماره پیگیری [trackingId] تأیید شد.»
- متن برای رد: «درخواست شما با شماره پیگیری [trackingId] رد شد. دلیل: [reason]»

### پیام داخلی (جدول user_messages)
```sql
CREATE TABLE user_messages (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    body TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT now()
);
```
پس از تأیید/رد، یک پیام داخلی برای کاربر ایجاد می‌شود. کاربر در بخش «پیام‌ها» می‌تواند آن را مشاهده کند.

---

## ۶. ملاحظات امنیتی

| تهدید | راهکار |
|--------|--------|
| دسترسی غیرمجاز به تیکت‌ها | APIهای `/admin/*` فقط با توکن مدیر پشتیبان سامانه قابل دسترسی هستند (بررسی role در دیتابیس) |
| مشاهده مدارک توسط دیگران | URLهای فایل‌ها یکبار مصرف یا دارای امضای زمانی (Signed URL) باشند. |
| اقدام بدون بررسی مدارک | در UI پشتیبان باید مدارک را ببیند و سپس اقدام کند. |
| سوءاستفاده از تأیید خودکار | تمام تأییدها در لاگ ثبت می‌شود. |

---

## ۷. خروجی نهایی

این صفحه مدیریت تیکت‌ها با قابلیت‌های زیر کامل شد:
- لیست تیکت‌ها با فیلتر و جستجو
- مشاهده جزئیات و مدارک
- تأیید و رد با ذکر دلیل
- ارسال اعلان (پیامک و پیام داخلی)
- ذخیره تاریخچه اقدامات

در صورت تأیید، صفحه **پیام‌های کاربر** (برای مشاهده اعلان‌ها و تیکت‌های خود) طراحی خواهد شد.