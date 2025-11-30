import os
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from tqdm import tqdm

# --- 💖 設定はここをいじるだけ！ 💖 ---

# 1. Google Drive の画像があるパスを設定
# Colabじゃないから、VS CodeがあるPCのローカルパスを入力してね！
# 例：C:/Users/User/Pictures/sleep_images/
IMAGE_DIR = "C:/Users/YourName/Desktop/sleep_images" # <--- ★あなたのPCの画像フォルダのパスに変更★

# 2. BGMファイルのパスを設定
BGM_PATH = "C:/Users/YourName/Desktop/lullaby_bgm.mp3" # <--- ★あなたのPCのBGMファイルのパスに変更★

# 3. 最終的な動画の長さ (秒) を設定
# 例：1時間 = 3600秒 / 10時間 = 36000秒
TARGET_DURATION_SECONDS = 3600 # 1時間（テスト用に短くしてもOK）

# 4. 1枚の画像を表示する時間 (秒) を設定
# 長すぎると単調、短すぎるとチカチカするから注意！
IMAGE_DURATION_SECONDS = 15 

# --- 💖 動画生成関数 💖 ---

def create_looped_video():
    print("--- 🎬 動画生成スタート！ 🎬 ---")
    
    # フォルダ内の画像ファイルを取得
    image_files = [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"🚨 エラー：指定されたフォルダに画像ファイルが見つかりません: {IMAGE_DIR}")
        return

    print(f"✅ 画像 {len(image_files)} 枚と BGM '{os.path.basename(BGM_PATH)}' を使います。")
    print(f"✅ 目標動画時間: {TARGET_DURATION_SECONDS // 60} 分")

    # ------------------------------------------------
    # 1. 映像クリップの作成とループ
    # ------------------------------------------------
    
    video_clips = []
    current_time = 0
    
    # tqdmで進捗バーを表示するよん！
    with tqdm(total=TARGET_DURATION_SECONDS, desc="🎥 映像クリップ作成＆ループ") as pbar:
        while current_time < TARGET_DURATION_SECONDS:
            for img_path in image_files:
                if current_time >= TARGET_DURATION_SECONDS:
                    break
                
                # 画像を読み込み、サイズを調整してクリップ化
                img_clip = ImageClip(img_path, duration=IMAGE_DURATION_SECONDS)
                
                # HDサイズ(1920x1080)に合わせる（中央配置）
                img = Image.open(img_path)
                width, height = img.size
                if width != 1920 or height != 1080:
                    # 画像がHDサイズでない場合、fitで中央配置し、背景は黒にする
                    print(f"⚠️ 画像 '{os.path.basename(img_path)}' のサイズがHDではないため調整します。")
                    img_clip = img_clip.resize(height=1080) # 高さで合わせる
                    # TODO: 必要であれば、ここで背景を黒で埋める処理を追加
                
                video_clips.append(img_clip)
                current_time += IMAGE_DURATION_SECONDS
                pbar.update(IMAGE_DURATION_SECONDS)
                
    # 結合して、目標時間でカットする
    final_video_clip = concatenate_videoclips(video_clips).set_duration(TARGET_DURATION_SECONDS)
    
    print("\n✅ 映像クリップ作成完了！")
    
    # ------------------------------------------------
    # 2. BGMの追加とループ
    # ------------------------------------------------
    
    if os.path.exists(BGM_PATH):
        print("🎶 BGMをループして設定します...")
        audio_clip = AudioFileClip(BGM_PATH)
        
        # BGMを動画の時間に合わせてループさせる
        looped_audio = audio_clip.loop(duration=TARGET_DURATION_SECONDS)
        
        final_video_clip = final_video_clip.set_audio(looped_audio)
        print("✅ BGM設定完了！")
    else:
        print(f"🚨 エラー：BGMファイルが見つかりません: {BGM_PATH}。BGMなしで書き出します。")
        
    # ------------------------------------------------
    # 3. ファイルの書き出し
    # ------------------------------------------------
    
    output_filename = f"Lullaby_Loop_{TARGET_DURATION_SECONDS // 60}min.mp4"
    print(f"\n💾 ファイル書き出し中... '{output_filename}'")
    
    final_video_clip.write_videofile(
        output_filename,
        codec='libx264',       # 標準的なエンコーダー
        audio_codec='aac',     # 標準的なオーディオエンコーダー
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        fps=24,                # フレームレートは低くてもOK（睡眠導入のため）
        threads=4              # PCのコア数に合わせて調整すると高速化するかも
    )
    
    print("\n--- ✨ 動画生成完了！超お疲れさま！ ✨ ---")
    print(f"🎉 ファイル名: {output_filename}")


if __name__ == "__main__":
    create_looped_video()
