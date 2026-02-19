curl --location 'https://open.tiktokapis.com/v2/post/publish/video/init/' \
--header 'Authorization: Bearer act.example12345Example12345Example' \
--header 'Content-Type: application/json; charset=UTF-8' \
--data-raw '{
  "post_info": {
    "title": "this will be a funny #cat video on your @tiktok #fyp",
    "privacy_level": "MUTUAL_FOLLOW_FRIENDS",
    "disable_duet": false,
    "disable_comment": true,
    "disable_stitch": false,
    "video_cover_timestamp_ms": 1000
  },
  "source_info": {
      "source": "FILE_UPLOAD",
      "video_size": 50000123,
      "chunk_size":  10000000,
      "total_chunk_count": 5
  }
}'


curl --location 'https://open.tiktokapis.com/v2/post/publish/video/init/' \
--header 'Authorization: Bearer act.BeHIY1zcMetD6e3VPuhnE2d59e6QGGdLY1x36oibNhvsyaLco31XwU8LJLez!5163.va' \
--header 'Content-Type: application/json; charset=UTF-8' \
--data-raw '{
  "post_info": {
    "title": "this will be a funny #cat video on your @tiktok #fyp",
    "privacy_level": "SELF_ONLY",
    "disable_duet": false,
    "disable_comment": true,
    "disable_stitch": false,
    "video_cover_timestamp_ms": 1000
  },
  "source_info": {
      "source": "PULL_FROM_URL",
      "video_url": "https://app.adsuhu.com/vit_ads_suhu_inherit/static/BigBuckBunny2.mp4"
  }
}'
