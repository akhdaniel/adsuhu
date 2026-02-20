
# FB post curl 

# 0) set vars AdSuhu3
APP_ID="2121157978717050"
APP_SECRET="92e087aa107d163222d0d5c3e1f1e555"
REDIRECT_URI="https://app.adsuhu.com/facebook/oauth/callback"
GRAPH_VER="v19.0"

# 0) set vars AdSuhu
APP_ID="1512596596516735"
APP_SECRET="5a25bd22b0269fab9d912fbd5e338879"
REDIRECT_URI="https://app.adsuhu.com/facebook/oauth/callback"
GRAPH_VER="v19.0"


# 1) generate OAuth URL (open this in browser, approve, then copy ?code=... from redirect)
echo "https://www.facebook.com/${GRAPH_VER}/dialog/oauth?client_id=${APP_ID}&redirect_uri=${REDIRECT_URI}&scope=pages_show_list,pages_manage_posts,pages_read_engagement,pages_manage_metadata&response_type=code"


# 2) exchange code -> user access token
CODE="AQAOMV8YRiuewQ29fpA-Y1Q7EwQRgEK6xku511ugT0xrSwXlpM7rroglf00QH-0Q_Rjqgk0jDlJJaEDIHKxNGyswzB9JWFpL52oDN-ER1wcDejoCovFHh0mA6XuXvMDtVOz29lrr6eYs3teu61KmpFwi_rDiO5gtadExqInWACQoFW7_dEPljmVSPP0VJZB_V1-lmyoxg218igHZF_qxniU_CiMJpr9wVKxvPcU3HGt51QRD2_4x_RxXdzF6yLZJGVoQyfYKnLO-lmxOawFSWt83Ht9M7E3I-L7f5ND_bF3viTTFztRBHvkCTSpiAbSE7ZH51YoLlFyseMiWXUeUpVUW3LLcb4Hodzi5cS5GyQdr1NOdEz5u4BX-sqX3a0_3UjZJSgeJDzatQP0-IvW5PsdPqLgd2HIqY7dJtonv7Hc9lw"
USER_TOKEN=$(curl -sG "https://graph.facebook.com/${GRAPH_VER}/oauth/access_token" \
  --data-urlencode "client_id=${APP_ID}" \
  --data-urlencode "client_secret=${APP_SECRET}" \
  --data-urlencode "redirect_uri=${REDIRECT_URI}" \
  --data-urlencode "code=${CODE}" | jq -r '.access_token')

echo "$USER_TOKEN"


# 3) get pages + page access token
curl -sG "https://graph.facebook.com/${GRAPH_VER}/me/accounts" \
  --data-urlencode "access_token=${USER_TOKEN}" \
  --data-urlencode "fields=id,name,access_token"


# 4) post image to page
PAGE_ID="YOUR_PAGE_ID"
PAGE_TOKEN="YOUR_PAGE_ACCESS_TOKEN"
IMAGE_URL="https://example.com/image.jpg"
MESSAGE="Hello from curl"

curl -sX POST "https://graph.facebook.com/${GRAPH_VER}/${PAGE_ID}/photos" \
  --data-urlencode "url=${IMAGE_URL}" \
  --data-urlencode "caption=${MESSAGE}" \
  --data-urlencode "access_token=${PAGE_TOKEN}"
