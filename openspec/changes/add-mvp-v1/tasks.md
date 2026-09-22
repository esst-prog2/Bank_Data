# Tasks: Add MVP v1

## 1. Data sources (prerequisite — see AGENTS.md "Immediate next steps")

- [ ] 1.1 Verify `data_acquisition/edap_scraper.py` against the live P3DH page
      (`--headed`, `playwright codegen` pass); resolve the Entity-slicer (LEI vs.
      display name) and Module/Template list open questions
- [ ] 1.2 Populate `data/entities.csv` from a real EBA Transparency Exercise
      participant list, trimmed to the pilot banks v1 will support
- [ ] 1.3 Create `data/modules.txt` with the exact disclosure module/template
      codes the pilot banks submit

## 2. Package surface

- [ ] 2.1 Define the public function signature: bank identifier, reporting
      period, requested variables -> pandas DataFrame
- [ ] 2.2 Define the DataFrame's columns: value, source reporting item,
      standardized concept, comparability flag/reason, missing-vs-failed status

## 3. Reconciliation logic

- [ ] 3.1 Build the source-item -> standardized-concept mapping for the pilot
      banks' variables
- [ ] 3.2 Implement the comparability check (flag genuinely non-comparable
      figures instead of combining them)
- [ ] 3.3 Distinguish "missing from source" from "retrieval/processing failed"
      end to end (acquisition layer already raises loudly per AGENTS.md's
      working conventions — surface that distinction through to the DataFrame)

## 4. Verification (see proposal's acceptance criteria / README section 4)

- [ ] 4.1 Test: given a supported bank + period + available variable, the
      returned value has correct source item and standardized-concept mapping
- [ ] 4.2 Test: given a variable genuinely absent from source, it's identified
      as missing-from-source, not as a retrieval/processing failure
- [ ] 4.3 Test: given two figures that cannot be established as economically
      equivalent, they're flagged non-comparable and not combined
- [ ] 4.4 Archive this change into `openspec/specs/data-retrieval/` once the
      above pass
