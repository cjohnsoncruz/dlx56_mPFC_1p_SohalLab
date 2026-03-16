# Decoding Pipeline State Diagram — `revisions_linear_classifiers_v6_subsample_ens.ipynb`

```mermaid
flowchart TD
    %% ──────────────── SETUP PHASE ────────────────
    START([Notebook Start]) --> SETUP

    subgraph SETUP ["1. Setup & Config (Cells 0-2)"]
        direction TB
        S1[Load libraries, configs<br/>config.yaml + analysis_config.yaml]
        S1 --> S2[Create run_output_dir<br/>results/shuffles/shuffle_run_RUN_ID/]
        S2 --> SAVE_CONFIG[/"💾 config_used.yaml<br/>(copy to run_output_dir)"/]
    end

    SETUP --> IMPORT

    subgraph IMPORT ["2. Data Import (Cells 3-5)"]
        direction TB
        I1[Load trial time-series parquet<br/>dff or raster data]
        I1 --> I2[Extract stage_names, numeric_col,<br/>unit_mean_tseries, subject_stage_info_df]
        I2 --> I3[Create date-stamped output_folder<br/>results/figure_5_prep_mid_decoding figures_{data_type}_{date}/]
        I3 --> I4[Create figure subfolders<br/>pdf/, png/, svg/]
        I4 --> SAVE_HYPER[/"💾 hyper_param_dict.json"/]
        I4 --> SAVE_SOURCE_TXT[/"💾 latest_figure_5_decode_setup_<br/>run_source_data.txt"/]
    end

    IMPORT --> ENRICH

    subgraph ENRICH ["3. Enrichment & Viz (Cells 8-11)"]
        direction TB
        E1[Define class_comparisons<br/>8 phase pairs for decoding]
        E1 --> E2[Compute trial counts &<br/>neuron enrichment by subject]
        E2 --> E3[Generate enrichment summary heatmaps]
        E3 --> SAVE_ENRICH_FIG[/"💾 Enrichment of cells...<br/>.pdf + .png"/]
    end

    ENRICH --> DATAPREP

    subgraph DATAPREP ["4. Data Preparation (Cells 14-24)"]
        direction TB
        D1[Build enrich_unit_ID_by_name_df<br/>dataset_name_by_geno_day]
        D1 --> D2["Build class_matrix_store<br/>(3-level nested dict:<br/>enrichment_phase → activity_phase → geno_day → subject_df)"]
    end

    DATAPREP --> GATE["🎛️ Gating Flags (Cell 20)"]

    %% ──────────────── 7 GATED BRANCHES ────────────────

    GATE -->|run_activity_save| ACT
    GATE -->|run_binary_SVM| SVM
    GATE -->|run_CCGP_base| CCGP
    GATE -->|run_CCGP_permuted| CCGP_PERM
    GATE -->|run_CCGP_wholepop| WPOP
    GATE -->|run_CCGP_wholepop_permuted| WPOP_PERM
    GATE -->|run_timedep| TIMEDEP

    %% ── Branch 1: Activity Save ──
    subgraph ACT ["Branch 1: Cell Activity Save (Cell 28)"]
        direction TB
        A1["For each bootstrap × ensemble × geno_day × train/test pair:<br/>resample → build matrices → record cell IDs + mean activity per class"]
        A1 --> SAVE_ACT[/"💾 Cell Activity (Out of Distrib)<br/>{n_activity_bootstraps} pseudopop<br/>{data_type} {date}.parquet"/]
    end

    %% ── Branch 2: Binary SVM In-Distribution ──
    subgraph SVM ["Branch 2: In-Distribution Binary SVM (Cells 32-37)"]
        direction TB
        B1["For each pseudopop_run × ensemble × geno_day × class_pair:<br/>resample → StratifiedShuffleSplit CV → LinearSVC"]
        B1 --> B2[Parallel via joblib<br/>n_jobs workers × chunked ranges]
        B2 --> B3[Package scores + weights]
        B3 --> SAVE_SVM_SCORES[/"💾 Decode enrich_unit<br/>{n_pseudopop_runs} pseudopop<br/>{data_type} {date}.parquet"/]
        B3 --> SAVE_SVM_WEIGHTS[/"💾 binary_SVM_weights_enrich_unit_<br/>{n}_pseudopop_{data_type}_{date}.parquet"/]
        B3 --> SAVE_SVM_TXT[/"💾 last_decoding_run_info.txt"/]
    end

    %% ── Branch 3: CCGP Base ──
    subgraph CCGP ["Branch 3: Out-of-Distribution CCGP (Cell 44)"]
        direction TB
        C1["For each pseudopop_run × ensemble × geno_day:<br/>resample → train on pair A, test on pair B<br/>align cells across train/test → LinearSVC"]
        C1 --> C2[Parallel via joblib]
        C2 --> C3[Package scores + weights]
        C3 --> SAVE_CCGP_SCORES[/"💾 Decode (Out of Distrib)<br/>{n_pseudopop_runs} pseudopop<br/>{data_type} {date}.parquet"/]
        C3 --> SAVE_CCGP_WEIGHTS[/"💾 out_distrib_SVM_weights_<br/>enrich_unit_{n}_pseudopop_<br/>{data_type}_{date}.parquet"/]
        C3 --> SAVE_CCGP_TXT[/"💾 last_generalize_decoding_run_info.txt"/]
    end

    %% ── Branch 4: CCGP Label-Permuted ──
    subgraph CCGP_PERM ["Branch 4: Label-Permuted CCGP (Cell 47)"]
        direction TB
        CP1["Same as Branch 3 but<br/>shuffle_labels=True<br/>(training labels randomly permuted)"]
        CP1 --> CP2[Parallel via joblib]
        CP2 --> CP3[Package scores + weights]
        CP3 --> SAVE_CCGP_PERM_SCORES[/"💾 Decode (LABEL PERMUTE-<br/>Out of Distrib) {n} pseudopop<br/>{data_type} {date}.parquet"/]
        CP3 --> SAVE_CCGP_PERM_WEIGHTS[/"💾 whole_pop_SVM_weights_<br/>{n}_pseudopop_{data_type}_{date}.parquet"/]
    end

    %% ── Branch 5: Whole-Pop CCGP ──
    subgraph WPOP ["Branch 5: Whole-Pop CCGP (Cells 53-56)"]
        direction TB
        W1["Merge ALL cells across ensembles<br/>(deduplicate per subject) → whole-pop matrix"]
        W1 --> W2["For each pseudopop_run × geno_day:<br/>resample whole pop → train/test out-of-distrib<br/>align common units → LinearSVC"]
        W2 --> W3[Parallel via joblib]
        W3 --> W4[Package scores + weights]
        W4 --> SAVE_WPOP_SCORES[/"💾 Decode (Out of Distrib Whole Pop)<br/>{n} pseudopop {data_type} {date}.parquet"/]
        W4 --> SAVE_WPOP_WEIGHTS[/"💾 whole_pop_SVM_weights_<br/>{n}_pseudopop_{data_type}_{date}.parquet"/]
    end

    %% ── Branch 6: Whole-Pop CCGP Permuted ──
    subgraph WPOP_PERM ["Branch 6: Whole-Pop CCGP Permuted (Cells 58-61)"]
        direction TB
        WP1["Same as Branch 5 but<br/>shuffle_labels=True"]
        WP1 --> WP2[Parallel via joblib]
        WP2 --> WP3[Package scores + weights]
        WP3 --> SAVE_WPOP_PERM_SCORES[/"💾 Decode (PERMUTED Out of Distrib<br/>Whole Pop) {n} pseudopop<br/>{data_type} {date}.parquet"/]
        WP3 --> SAVE_WPOP_PERM_WEIGHTS[/"💾 whole_pop_permuted_SVM_weights_<br/>{n}_pseudopop_{data_type}_{date}.parquet"/]
    end

    %% ── Branch 7: Time-Dependent Decoding ──
    subgraph TIMEDEP ["Branch 7: Time-Dependent Decoding (Cells 63-67)"]
        direction TB
        T1["Slice time-series into frame bins<br/>(frame_batch_size windows)"]
        T1 --> T2["For each bootstrap × ensemble × geno_day × class_pair × time_bin:<br/>resample → ShuffleSplit CV → LinearSVC per bin"]
        T2 --> T3["Parallel via joblib<br/>(mmap class_matrix_store to disk<br/>to avoid per-worker pickle cost)"]
        T3 --> T4[Package scores<br/>no weights saved — MemoryError prevention]
        T4 --> SAVE_TD_SCORES[/"💾 Timebin {batch}_window Decoding-<br/>{n}_bootstrap {data_type} {date}.parquet"/]
        T4 --> SAVE_TD_TXT[/"💾 last_time_decoding_run_info.txt"/]
    end

    %% ──────────────── FINAL SUMMARY ────────────────
    ACT --> SUMMARY
    SVM --> SUMMARY
    CCGP --> SUMMARY
    CCGP_PERM --> SUMMARY
    WPOP --> SUMMARY
    WPOP_PERM --> SUMMARY
    TIMEDEP --> SUMMARY

    subgraph SUMMARY ["5. Run Record Summary (Cells 71-73)"]
        direction TB
        R1["Collect run info from all<br/>completed branches:<br/>date, decoding_type, dataset,<br/>output filenames, weight filenames"]
        R1 --> R2["Load or create master CSV<br/>append current run info"]
        R2 --> SAVE_RECORD[/"💾 Decoder- Out of Distribution -<br/>run version record.csv"/]
    end

    SUMMARY --> DONE([Notebook End])

    %% ──────────────── STYLING ────────────────
    classDef saveNode fill:#2d6a4f,stroke:#1b4332,color:#fff,font-size:11px
    classDef gateNode fill:#e76f51,stroke:#d62828,color:#fff,font-weight:bold
    classDef setupBox fill:#264653,stroke:#2a9d8f,color:#fff
    classDef branchBox fill:#023047,stroke:#219ebc,color:#fff

    class SAVE_CONFIG,SAVE_HYPER,SAVE_SOURCE_TXT,SAVE_ENRICH_FIG saveNode
    class SAVE_ACT,SAVE_SVM_SCORES,SAVE_SVM_WEIGHTS,SAVE_SVM_TXT saveNode
    class SAVE_CCGP_SCORES,SAVE_CCGP_WEIGHTS,SAVE_CCGP_TXT saveNode
    class SAVE_CCGP_PERM_SCORES,SAVE_CCGP_PERM_WEIGHTS saveNode
    class SAVE_WPOP_SCORES,SAVE_WPOP_WEIGHTS saveNode
    class SAVE_WPOP_PERM_SCORES,SAVE_WPOP_PERM_WEIGHTS saveNode
    class SAVE_TD_SCORES,SAVE_TD_TXT saveNode
    class SAVE_RECORD saveNode
    class GATE gateNode
```

## Output File Inventory

### Always Saved (unconditional)
| Output File | Saved At | Description |
|---|---|---|
| `config_used.yaml` | Cell 2 | Copy of config snapshot for reproducibility |
| `hyper_param_dict.json` | Cell 5 | Preprocessing hyperparameters |
| `latest_figure_5_decode_setup_run_source_data.txt` | Cell 5 | Source dataset filename record |
| `Enrichment of cells... .pdf/.png` | Cell 11 | Summary heatmaps of trial counts & enrichment |
| `Decoder- Out of Distribution - run version record.csv` | Cell 73 | Append-only master log of all decoding runs |

### Conditionally Saved (gated by flags in Cell 20)
| Flag | Scores File | Weights File | Metadata File |
|---|---|---|---|
| `run_activity_save` | `Cell Activity (Out of Distrib) *.parquet` | — | — |
| `run_binary_SVM` | `Decode enrich_unit *.parquet` | `binary_SVM_weights_enrich_unit_*.parquet` | `last_decoding_run_info.txt` |
| `run_CCGP_base` | `Decode (Out of Distrib) *.parquet` | `out_distrib_SVM_weights_enrich_unit_*.parquet` | `last_generalize_decoding_run_info.txt` |
| `run_CCGP_permuted` | `Decode (LABEL PERMUTE- Out of Distrib) *.parquet` | `whole_pop_SVM_weights_*.parquet` | — |
| `run_CCGP_wholepop` | `Decode (Out of Distrib Whole Pop) *.parquet` | `whole_pop_SVM_weights_*.parquet` | — |
| `run_CCGP_wholepop_permuted` | `Decode (PERMUTED Out of Distrib Whole Pop) *.parquet` | `whole_pop_permuted_SVM_weights_*.parquet` | — |
| `run_timedep` | `Timebin {batch}_window Decoding- *.parquet` | *(removed — MemoryError)* | `last_time_decoding_run_info.txt` |
