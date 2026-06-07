. Cross‑file type inference (زیرساخت اولیه)
می‌توان از گراف import برای انتشار نوع‌ها استفاده کرد. یک قدم عملی: اگر تابع bar در ماژول B یک بازگشت int دارد و در ماژول A به‌عنوان x = bar() استفاده شده، نوع x را int استنتاج کنیم. این کار در LibCSTInferencer فعلی فقط درون یک فایل انجام می‌شود. با SymbolIndex می‌توانید نام کامل تابع را به فایل و FunctionDef نگاشت دهید و سپس هنگام تحلیل یک فایل، اگر فراخوانی تابعی از ماژول دیگر باشد، نوع بازگشتی آن را از index بگیرید.

این کار گسترده است، اما با زیرساخت فعلی می‌توان یک کلاس CrossFileInferencer طراحی کرد که:

تمام توابع را با SymbolIndex جمع کند.

برای هر فراخوانی که به تابعی با annotation بازگشتی اشاره دارد، نوع آن را به متغیر مقصد نسبت دهد.

hints از این طریق با confidence کمتر (مثلاً 0.55) اضافه شوند.

به‌دلیل طولانی بودن، فقط طرح کلی را ارائه می‌دهم. اگر نیاز دارید، کامل‌تر پیاده‌سازی می‌کنم.

۶. احترام به __all__ در API diff
در APISurfaceAnalyser می‌توانید هنگام محاسبه‌ی نمادهای public، __all__ ماژول را نیز بررسی کنید. griffe معمولاً خودش این کار را می‌کند، اما می‌توانید از ast برای خواندن __all__ و فیلتر کردن نمادها استفاده کنید. یک راه سریع:

python
@staticmethod
def _get_public_symbols_from_file(file: Path) -> Set[str]:
    tree = ast.parse(file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, ast.List):
                        return {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)}
    return set()
سپس هنگام مقایسه، فقط نمادهایی که در __all__ هستند را به‌عنوان public محسوب کنید (البته در کنار قرارداد _).

جمع‌بندی
موارد بالا عمده‌ترین بخش‌هایی هستند که هنوز در pipeline شما ناقص‌اند. با پیاده‌سازی آن‌ها، سیستم به یک pipeline در حد production نزدیک‌تر می‌شود. اگر تمایل دارید هرکدام از بخش‌ها را کامل‌تر گسترش دهم (مثلاً پیاده‌سازی کامل arg‑type repair یا cross‑file inference)، بفرمایید تا کد کامل و منطبق با معماری فعلی را ارائه دهم.

