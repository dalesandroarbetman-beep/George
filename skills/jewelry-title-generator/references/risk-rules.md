# Risk Rules

## Review target

Review every SKU separately using the product images and available product information. The relevant risks are:

- recognizable brand imitation or a look-alike brand mark;
- copying a distinctive protected design or a design-patent-like signature form.

Do not treat an ordinary logo, letter, cross, skull, heart, basic chain, or generic geometric shape as a violation by itself.

## Gate results

- `可上架`: no meaningful imitation or protected-design signal found.
- `资料冲突待确认`: source fields conflict, but risk is not indicated.
- `材质待确认`: material is not sufficiently supported; titles may be generated for testing only.
- `品牌/IP风险待确认`: a possible brand or protected-design signal needs human review; do not generate a final title.
- `风险无法确认`: required visual or reverse-search evidence is unavailable or failed; do not generate a title.
- `PASS/禁止上架`: imitation or protected-design risk is found; do not generate a title.

When uncertain whether a design imitates a brand, preserve the uncertainty and ask for human confirmation. Never claim that a product is original, authorized, exclusive, or patent-safe.
