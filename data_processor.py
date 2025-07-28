#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水啦！WATER LIVES HERE 展覽報名資料處理腳本
"""

import pandas as pd
import os
import json
from datetime import datetime
import pytz

def load_project_config():
    """載入專案設定"""
    with open('project_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def read_historical_data():
    """讀取歷史資料"""
    merged_file = 'WaterLivesHere-Dashboard-Test/merged_attendees.csv'
    if os.path.exists(merged_file):
        return pd.read_csv(merged_file, encoding='utf-8')
    else:
        # 如果沒有歷史資料，建立空的 DataFrame
        return pd.DataFrame(columns=['訂單編號', '參加人姓名', '參加人Email', '參加人電話', 
                                   '價錢', '票種', '狀態', '建立時間', '活動類型'])

def process_raw_data():
    """處理原始資料"""
    raw_data_dir = 'WaterLivesHere-Dashboard-Test/raw_data'
    all_data = []
    
    # 遍歷原始資料目錄
    for filename in os.listdir(raw_data_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(raw_data_dir, filename)
            print(f"處理檔案: {filename}")
            
            # 讀取 CSV 檔案
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 檢查是否有訂單編號欄位
            if '訂單編號' not in df.columns:
                print(f"警告: {filename} 中缺少訂單編號欄位")
                continue
            
            # 資料清理
            df = df.dropna(subset=['參加人姓名', '參加人Email'])  # 移除關鍵欄位為空的記錄
            df['參加人電話'] = df['參加人電話'].astype(str)  # 確保電話號碼為字串
            
            all_data.append(df)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

def upsert_data(historical_df, new_df):
    """執行資料去重與合併 (Upsert)"""
    if new_df.empty:
        return historical_df
    
    # 以參加人Email為唯一鍵進行去重
    # 如果有新的資料，則更新；如果沒有，則新增
    combined_df = pd.concat([historical_df, new_df], ignore_index=True)
    
    # 按照Email去重，保留最新的記錄
    combined_df = combined_df.drop_duplicates(subset=['參加人Email'], keep='last')
    
    return combined_df

def save_merged_data(df):
    """安全儲存合併後的資料"""
    output_dir = 'WaterLivesHere-Dashboard-Test'
    temp_file = os.path.join(output_dir, 'merged_attendees.tmp.csv')
    final_file = os.path.join(output_dir, 'merged_attendees.csv')
    
    # 先寫入臨時檔案
    df.to_csv(temp_file, index=False, encoding='utf-8')
    
    # 成功後重新命名為正式檔案
    os.rename(temp_file, final_file)
    print(f"資料已儲存至: {final_file}")

def move_processed_files():
    """將處理過的原始檔案移動到 processed_data 目錄"""
    raw_data_dir = 'WaterLivesHere-Dashboard-Test/raw_data'
    processed_data_dir = 'WaterLivesHere-Dashboard-Test/processed_data'
    
    # 確保 processed_data 目錄存在
    os.makedirs(processed_data_dir, exist_ok=True)
    
    for filename in os.listdir(raw_data_dir):
        if filename.endswith('.csv'):
            src = os.path.join(raw_data_dir, filename)
            dst = os.path.join(processed_data_dir, filename)
            os.rename(src, dst)
            print(f"已移動檔案: {filename} -> processed_data/")

def main():
    """主函數"""
    print("開始處理資料...")
    
    # 載入專案設定
    config = load_project_config()
    print(f"專案名稱: {config['project_name']}")
    
    # 讀取歷史資料
    historical_df = read_historical_data()
    print(f"歷史資料筆數: {len(historical_df)}")
    
    # 處理新資料
    new_df = process_raw_data()
    print(f"新資料筆數: {len(new_df)}")
    
    if new_df.empty:
        print("沒有新資料需要處理")
        return
    
    # 執行資料合併
    merged_df = upsert_data(historical_df, new_df)
    print(f"合併後總筆數: {len(merged_df)}")
    
    # 儲存合併後的資料
    save_merged_data(merged_df)
    
    # 移動已處理的檔案
    move_processed_files()
    
    # 生成分析結果
    analysis_results = {
        'total_attendees': len(merged_df),
        'early_bird_count': len(merged_df[merged_df['活動類型'] == '早早鳥']),
        'regular_bird_count': len(merged_df[merged_df['活動類型'] == '早鳥']),
        'last_updated': datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S'),
        'update_date': datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d')
    }
    
    # 儲存分析結果
    with open('WaterLivesHere-Dashboard-Test/analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    print("資料處理完成!")
    print(f"總報名人數: {analysis_results['total_attendees']}")
    print(f"早早鳥: {analysis_results['early_bird_count']}")
    print(f"早鳥: {analysis_results['regular_bird_count']}")

if __name__ == "__main__":
    main()

