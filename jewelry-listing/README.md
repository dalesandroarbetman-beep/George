# 饰品独立站上品工作流

本项目为单 SKU 饰品上品准备可审核的数据包。流程会先核对商品资料、主图和尺寸图，再执行标题与品牌/IP 风险闸门；缺少尺寸信息、资料冲突或风险无法确认时会暂停，不打开或提交后台表单。

## 主要能力

- `skills/jewelry-title-generator/`：生成标题候选并进行品牌/IP、材质和措辞风险审核。
- `skills/jewelry-auto-listing/`：生成 `上品包.json`、图片索引和中文审核清单。
- `contracts/jewelry-listing-v1.2.schema.json`：约束上品包的数据结构和暂停条件。
- `auto_listing.py`：兼容入口，调用 Skill 中的唯一实现。

## 本地运行

```powershell
py -3 auto_listing.py XX50438B0W0 `
  --record "商品资料.xlsx" `
  --source-root "C:\path\to\source-root" `
  --review-root "C:\path\to\review-root"
```

也可双击 `开始单SKU上品.bat`。真实后台提交不在本地脚本中实现；只有用户明确授权、上品包通过人工审核且复用现有登录会话时，才能继续后台操作。
