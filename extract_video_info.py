# filename: extract_video_info.py

from pytube import YouTube

def extract_video_info(url):
    try:
        yt = YouTube(url)
        return {
            "title": yt.title,
            "views": yt.views,
            "likes": yt.like_count,
            "dislikes": yt.dislike_count,
            "channel": yt.channel_url,
            "thumbnail": yt.thumbnail_url,
            "description": yt.description,
        }
    except Exception as e:
        return f"Erro ao extrair informações do vídeo: {str(e)}"

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=qsG0-KZVZMY"
    video_info = extract_video_info(url)
    print(video_info)
