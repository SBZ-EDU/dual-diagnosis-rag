# استقرار در دو حالت

## حالت ۱ — فقط Hugging Face
اپ و API روی Hugging Face اجرا می‌شوند. `FIREBASE_ENABLED=0` باشد. Secrets لازم: در صورت نیاز `HF_TOKEN`، `WANDB_API_KEY`.

## حالت ۲ — Hugging Face + Firebase
مدل/RAG روی HF و داده ساخت‌یافته روی Firestore است.

1. در Firebase Console پروژه و Firestore را بسازید.
2. Authentication را فعال و برای کاربران بالینی Custom Claim به نام `role=clinician` تعیین کنید.
3. از پوشه `firebase/` اجرا کنید: `firebase deploy --only firestore`.
4. Service Account محدود بسازید؛ JSON را هرگز commit نکنید.
5. در Secrets میزبان تنظیم کنید:
   - `FIREBASE_ENABLED=1`
   - `FIREBASE_PROJECT_ID`
   - `PATIENT_ID_SALT` (تصادفی و طولانی)
   - `GOOGLE_APPLICATION_CREDENTIALS` یا credential استاندارد محیط
6. API `/risk` ارزیابی را ذخیره می‌کند و برای سطوح بالا/خیلی بالا/بحرانی Alert می‌سازد.

## مدل داده
- `patients/{hashedPatientId}`: فقط شناسه مستعار و زمان به‌روزرسانی
- `patients/{hashedPatientId}/assessments/{id}`: امتیاز، سطح و زمان
- `alerts/{id}`: هشدار قابل تأیید پزشک
- `articles/{id}`: متادیتای مقاله پس از بازبینی

## نکات امنیتی
- نام، کد ملی، شماره تماس و متن شناسایی‌کننده وارد نشود.
- Service Account فقط سمت سرور؛ هرگز در مرورگر، Git یا Dataset قرار نگیرد.
- Rules پیش‌فرض deny-all و دسترسی role-based هستند.
- برای داده واقعی پزشکی، قرارداد پردازش داده، محل نگهداری، رضایت بیمار، audit log، retention و الزامات قانونی ایران/کشور میزبان باید مستقل بررسی شوند.
- این سامانه درمان را خودکار تغییر نمی‌دهد؛ هشدار نیازمند بازبینی پزشک است.
