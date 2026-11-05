#!/bin/bash
# kks-tech.jp/leetenki_profile/ へ、GitHubに push 済みの内容（HEAD の git 管理ファイル）をそのまま配置する
#   bash _build/deploy_kks.sh
set -e
cd "$(dirname "$0")/.."
KEY=~/.ssh/mochi_aws.pem; HOST=ec2-user@54.250.208.179; REMOTE=/var/www/html/leetenki_profile
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
git archive HEAD | tar -x -C "$TMP"
rm -rf "$TMP/_build" "$TMP/.gitignore"
ssh -i $KEY $HOST "mkdir -p $REMOTE"
chmod 755 "$TMP"
rsync -az -e "ssh -i $KEY" "$TMP/" "$HOST:$REMOTE/"
for f in index.html en.html zh.html; do
  L=$(git show HEAD:$f | md5 -q); R=$(curl -sL "https://kks-tech.jp/leetenki_profile/$f?cb=$(date +%s)" | md5 -q)
  [ "$L" = "$R" ] && echo "OK  $f (md5 一致)" || { echo "NG: $f が不一致"; exit 1; }
done
echo "LIVE  https://kks-tech.jp/leetenki_profile/"
