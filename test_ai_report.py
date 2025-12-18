#!/usr/bin/env python3
"""
測試AI財務報告功能
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost/api"

def login():
    """登錄並獲取token"""
    # 使用測試帳號或實際帳號
    # 注意：這裡需要使用實際存在的帳號
    url = f"{BASE_URL}/auth/login"

    # FormData格式
    data = {
        "username": "test@example.com",  # 請替換為實際帳號
        "password": "Test1234!@#$"       # 請替換為實際密碼
    }

    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✓ 登錄成功")
            return token
        else:
            print(f"✗ 登錄失敗: {response.status_code}")
            print(f"  錯誤: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 登錄異常: {e}")
        return None

def test_ai_report(token):
    """測試AI財務報告API"""
    url = f"{BASE_URL}/reports/ai-financial-summary"

    # 設置日期範圍：最近30天
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }

    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"\n測試參數:")
    print(f"  開始日期: {params['start_date']}")
    print(f"  結束日期: {params['end_date']}")
    print(f"\n正在請求API...")

    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            print(f"✓ API請求成功!")

            data = response.json()

            # 顯示關鍵數據
            print(f"\n【報告摘要】")
            print(f"  報告期間: {data['report_period_start']} 至 {data['report_period_end']}")
            print(f"  生成時間: {data['report_generated_at']}")
            print(f"\n【財務概況】")
            print(f"  總收入: ${data['total_income']:,.2f}")
            print(f"  總支出: ${data['total_expense']:,.2f}")
            print(f"  淨收入: ${data['net_income']:,.2f}")
            print(f"  儲蓄率: {data['savings_rate']:.1f}%")
            print(f"\n【財務健康評分】")
            print(f"  評分: {data['financial_health_score']:.1f} / 100")

            if data['alerts']:
                print(f"\n【警示】")
                for alert in data['alerts']:
                    print(f"  ⚠️  {alert}")
            else:
                print(f"\n【警示】")
                print(f"  ✓ 無警示")

            print(f"\n【交易統計】")
            print(f"  交易總數: {data['total_transactions']}")
            print(f"  平均交易金額: ${data['average_transaction_amount']:,.2f}")
            print(f"  每日平均支出: ${data['daily_average_expense']:,.2f}")
            print(f"  支出趨勢: {data['expense_trend']}")

            print(f"\n【文本報告預覽】")
            print(f"  報告長度: {len(data['text_report'])} 字符")
            print(f"  前200字:")
            print("  " + "-" * 60)
            print("  " + data['text_report'][:200].replace("\n", "\n  "))
            print("  " + "-" * 60)

            # 保存完整報告
            filename = f"ai_report_{params['start_date']}_{params['end_date']}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(data['text_report'])
            print(f"\n✓ 完整報告已保存至: {filename}")

            return True
        else:
            print(f"✗ API請求失敗: {response.status_code}")
            print(f"  錯誤: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 請求異常: {e}")
        return False

def main():
    print("=" * 70)
    print("AI財務報告功能測試")
    print("=" * 70)

    # 步驟1: 登錄
    print("\n[1/2] 登錄系統...")
    token = login()

    if not token:
        print("\n✗ 測試失敗：無法登錄")
        print("\n請確認:")
        print("  1. Docker容器正在運行")
        print("  2. 修改腳本中的測試帳號和密碼")
        print("  3. 測試帳號已註冊")
        return

    # 步驟2: 測試AI報告API
    print("\n[2/2] 測試AI財務報告API...")
    success = test_ai_report(token)

    print("\n" + "=" * 70)
    if success:
        print("✓ 測試完成！所有功能正常運行")
    else:
        print("✗ 測試失敗！請檢查錯誤信息")
    print("=" * 70)

if __name__ == "__main__":
    main()
