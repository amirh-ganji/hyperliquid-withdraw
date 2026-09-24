"""
اسکریپت برداشت از Hyperliquid با استفاده از SDK رسمی
======================================================

نکات امنیتی مهم (حتماً بخونید):
1. این اسکریپت باید فقط روی کامپیوتر خودتون اجرا بشه، نه روی هیچ سرور یا سرویس شخص ثالث.
2. کلید خصوصی (private key) رو هرگز در جایی آپلود نکنید، به کسی ندید، و در گیت‌هاب/تلگرام/دیسکورد قرار ندید.
3. کلید رو از طریق متغیر محیطی (environment variable) وارد می‌کنیم، نه داخل کد.
4. قبل از اجرا، حتماً مستندات رسمی رو چک کنید چون نام متدهای SDK ممکنه تغییر کرده باشه:
   https://github.com/hyperliquid-dex/hyperliquid-python-sdk
   https://hyperliquid.gitbook.io/hyperliquid-docs/

نصب پیش‌نیازها:
    pip install hyperliquid-python-sdk

نحوه استفاده:
    مقادیر PRIVATE_KEY و WITHDRAW_ADDRESS رو در پایین همین فایل (داخل بخش مشخص‌شده)
    پر کنید و بعد فایل رو اجرا کنید:
        python3 hyperliquid_withdraw.py

    نکته: چون کلید خصوصی داخل همین فایل نوشته می‌شه، بعد از اتمام کار،
    یا فایل رو پاک کنید یا مقدار PRIVATE_KEY رو دوباره خالی (="") کنید،
    و هرگز این فایل رو (با کلید پر شده) با کسی به اشتراک نذارید یا آپلود نکنید.
"""

import os
import sys

try:
    from eth_account import Account
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from hyperliquid.utils import constants
except ImportError:
    print("لطفاً اول کتابخانه‌ها رو نصب کنید:")
    print("    pip install hyperliquid-python-sdk")
    sys.exit(1)


# ==============================================================
#  فقط همین دو خط زیر رو با اطلاعات خودتون پر کنید
#  (بقیه کد رو لازم نیست تغییر بدید)
# ==============================================================

PRIVATE_KEY = "00000000000000000000"        # <-- کلید خصوصی ولت هایپرلیکوئید خودتون رو اینجا بین "" بذارید
WITHDRAW_ADDRESS = "0x0000000000000"   # <-- آدرس متامسک آربیتروم خودتون رو اینجا بین "" بذارید

# ==============================================================
#  از این خط به پایین دیگه نیازی به تغییر نیست
# ==============================================================


def main():
    # اول از متغیرهای بالا می‌خونه؛ اگه خالی بود، از environment variable هم امتحان می‌کنه
    private_key = PRIVATE_KEY or os.getenv("HL_PRIVATE_KEY")
    withdraw_address = WITHDRAW_ADDRESS or os.getenv("HL_WITHDRAW_ADDRESS")

    if not private_key:
        print("خطا: مقدار PRIVATE_KEY رو در بالای فایل خالی گذاشتید.")
        print("برید بالای فایل و کلید خصوصی رو بین گیومه‌ها وارد کنید.")
        sys.exit(1)

    if not withdraw_address:
        print("خطا: مقدار WITHDRAW_ADDRESS رو در بالای فایل خالی گذاشتید.")
        print("برید بالای فایل و آدرس متامسک رو بین گیومه‌ها وارد کنید.")
        sys.exit(1)

    wallet = Account.from_key(private_key)
    address = wallet.address
    print(f"آدرس ولت شما: {address}")

    # اتصال به شبکه اصلی (mainnet)
    base_url = constants.MAINNET_API_URL
    info = Info(base_url, skip_ws=True)
    exchange = Exchange(wallet, base_url)

    # 1) بررسی وضعیت فعلی حساب (Perp و Spot)
    print("\n--- در حال بررسی موجودی ---")
    try:
        user_state = info.user_state(address)
        spot_state = info.spot_user_state(address)
        print("وضعیت Perp:", user_state.get("marginSummary", {}))
        print("وضعیت Spot:", spot_state.get("balances", []))
    except Exception as e:
        print(f"خطا در دریافت وضعیت حساب: {e}")
        sys.exit(1)

    perp_usdc = float(user_state.get("marginSummary", {}).get("accountValue", 0))
    print(f"\nموجودی تقریبی در Perp: {perp_usdc} USDC")

    if perp_usdc <= 0:
        print("موجودی قابل انتقالی در بخش Perp پیدا نشد.")
        return

    # 2) انتقال موجودی از Perp به Spot (در صورت نیاز)
    amount_to_move = round(perp_usdc - 1, 2)  # کمی مارجین برای کارمزد/تغییرات نگه می‌داریم
    if amount_to_move > 0:
        confirm = input(
            f"\nآیا می‌خواید {amount_to_move} USDC از Perp به Spot منتقل بشه؟ (yes/no): "
        )
        if confirm.strip().lower() == "yes":
            try:
                # نام دقیق متد ممکنه در نسخه‌های مختلف SDK فرق کنه - مستندات رو چک کنید
                result = exchange.usd_class_transfer(amount_to_move, to_perp=False)
                print("نتیجه انتقال Perp -> Spot:", result)
            except Exception as e:
                print(f"خطا در انتقال: {e}")
                sys.exit(1)

    # 3) برداشت از Spot به آدرس مقصد (روی شبکه Arbitrum)
    confirm2 = input(
        f"\nآیا می‌خواید موجودی به آدرس {withdraw_address} برداشت بشه؟ (yes/no): "
    )
    if confirm2.strip().lower() == "yes":
        withdraw_amount = input("مقدار USDC برای برداشت را وارد کنید: ")
        try:
            withdraw_amount = float(withdraw_amount)
            result = exchange.withdraw_from_bridge(withdraw_amount, withdraw_address)
            print("نتیجه برداشت:", result)
        except Exception as e:
            print(f"خطا در برداشت: {e}")
            sys.exit(1)

    print("\nتمام. لطفاً وضعیت آدرس مقصد رو در اکسپلورر Arbitrum (arbiscan.io) چک کنید.")


if __name__ == "__main__":
    main()