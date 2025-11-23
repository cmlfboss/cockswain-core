#!/usr/bin/env bash
INBOUND="/srv/cockswain-core/data/inbound"
REPO="/srv/cockswain-core/data/repo"

mkdir -p "$REPO"

for f in "$INBOUND"/*.json; do
  [ -e "$f" ] || continue

  topic=$(jq -r '.meta.topic' "$f" 2>/dev/null || echo "")

  case "$topic" in
    ecosys/mother/*)
      target="$REPO/02_node_build_logs"
      ;;
    ecosys/data/*)
      target="$REPO/01_ecosys_design"
      ;;
    ecosys/layout)
      target="$REPO/01_ecosys_design"
      ;;
    security/*)
      target="$REPO/02_node_build_logs"
      ;;
    helmsman/*)
      target="$REPO/03_helmsman_capability"
      ;;
    infra/*)
      target="$REPO/02_node_build_logs"
      ;;
    migration/*)
      target="$REPO/01_ecosys_design"
      ;;
    qa/*)
      target="$REPO/03_helmsman_capability"
      ;;
    chain/*)
      target="$REPO/04_chain_and_token"
      ;;
    *)
      target="$REPO/99_misc"
      ;;
  esac

  mkdir -p "$target"
  mv "$f" "$target"/
  echo "moved: $(basename "$f") -> $target"
done
