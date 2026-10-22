// LongBanana leaderboard data (inlined so the page works from file:// without a server).
// Source: paper-longbanana_open_ready_2 -> sec/5_experiments.tex (main tables)
//   - Table tab "strategy"  : Tab. strategy_comparison (Nano Banana 2 fixed as image generator)
//   - Table tab "generator" : Tab. generator_comparison_openclaw (OpenClaw + RPR fixed as controller)
// Subclass + suite + Overall "Avg." columns are checklist-average scores (0-100).
// P@70% is the difficulty-weighted task pass rate.
// Suite "Avg." = unweighted mean of its three subclasses (computed from the printed subclass values).
//
// row schema consumed by index.js:
//   { info:{name, type, typeLabel, backend},
//     overall:{overall:Avg, p70:P@70%},
//     topo:{overall, scc, rgc, lac},
//     appr:{overall, gac, lab, ahc},
//     reason:{overall, sel, tsr, agg} }

window.LB = {
  datasets: {
    strategy: {
      tabLabel: 'Controllers (Nano Banana 2 fixed)',
      metaHeaders: ['Name', 'Type', 'Backend'],
      desc:
        'Strategy comparison on the 90-case <b>LongBanana</b> benchmark with Nano Banana 2 fixed as the image generator. ' +
        'Subclass, suite and Overall <b>Avg.</b> columns use the checklist-average score converted to 0&ndash;100; ' +
        '<b>P@70%</b> is the difficulty-weighted task pass rate. ' +
        'The best value in each column is <b>in-bold</b>, the second best is <u>underlined</u>. ' +
        'Click a suite header (<i>Overall</i>, <i>Scene Composition</i>, &hellip;) to expand its subclass columns.',
      rows: [
        { info: { name: 'FP-Direct', type: 'direct', typeLabel: 'Direct', backend: 'Nano Banana 2' },
          overall: { overall: 68.4, p70: 24.4 },
          topo: { overall: 64.5, scc: 69.6, rgc: 61.8, lac: 62.0 },
          appr: { overall: 79.1, gac: 88.7, lab: 77.5, ahc: 71.1 },
          reason: { overall: 61.6, sel: 56.4, tsr: 73.4, agg: 55.1 } },

        { info: { name: 'PD-Direct', type: 'direct', typeLabel: 'Direct', backend: 'Nano Banana 2' },
          overall: { overall: 74.6, p70: 35.6 },
          topo: { overall: 64.8, scc: 69.9, rgc: 61.9, lac: 62.6 },
          appr: { overall: 86.0, gac: 98.8, lab: 87.0, ahc: 72.1 },
          reason: { overall: 73.1, sel: 68.5, tsr: 67.2, agg: 83.6 } },

        { info: { name: 'Hermes-Agent', type: 'harness', typeLabel: 'Harness', backend: 'Nano Banana 2' },
          overall: { overall: 73.9, p70: 43.3 },
          topo: { overall: 63.2, scc: 70.1, rgc: 61.5, lac: 57.9 },
          appr: { overall: 81.9, gac: 93.2, lab: 87.2, ahc: 65.4 },
          reason: { overall: 76.8, sel: 72.1, tsr: 75.1, agg: 83.1 } },

        { info: { name: 'OpenCode', type: 'harness', typeLabel: 'Harness', backend: 'Nano Banana 2' },
          overall: { overall: 77.3, p70: 47.8 },
          topo: { overall: 65.4, scc: 71.9, rgc: 62.3, lac: 62.1 },
          appr: { overall: 86.9, gac: 96.3, lab: 90.1, ahc: 74.2 },
          reason: { overall: 79.5, sel: 75.4, tsr: 77.8, agg: 85.2 } },

        { info: { name: 'OpenClaw', type: 'harness', typeLabel: 'Harness', backend: 'Nano Banana 2' },
          overall: { overall: 76.1, p70: 40.0 },
          topo: { overall: 65.3, scc: 71.8, rgc: 63.3, lac: 60.8 },
          appr: { overall: 86.6, gac: 96.8, lab: 88.3, ahc: 74.7 },
          reason: { overall: 76.4, sel: 70.3, tsr: 78.7, agg: 80.3 } },

        { info: { name: 'Hermes-Agent + RPR', type: 'harness_rpr', typeLabel: 'Harness +RPR', backend: 'Nano Banana 2' },
          overall: { overall: 75.6, p70: 35.6 },
          topo: { overall: 65.7, scc: 72.0, rgc: 64.0, lac: 61.0 },
          appr: { overall: 83.2, gac: 94.5, lab: 85.5, ahc: 69.5 },
          reason: { overall: 78.1, sel: 71.9, tsr: 76.1, agg: 86.2 } },

        { info: { name: 'OpenCode + RPR', type: 'harness_rpr', typeLabel: 'Harness +RPR', backend: 'Nano Banana 2' },
          overall: { overall: 77.8, p70: 43.3 },
          topo: { overall: 68.3, scc: 76.3, rgc: 64.6, lac: 64.1 },
          appr: { overall: 85.9, gac: 92.6, lab: 86.8, ahc: 78.2 },
          reason: { overall: 79.1, sel: 75.5, tsr: 76.5, agg: 85.3 } },

        { info: { name: 'OpenClaw + RPR', type: 'harness_rpr', typeLabel: 'Harness +RPR', backend: 'Nano Banana 2' },
          overall: { overall: 78.4, p70: 47.8 },
          topo: { overall: 68.2, scc: 76.1, rgc: 64.5, lac: 64.1 },
          appr: { overall: 87.1, gac: 97.1, lab: 88.6, ahc: 75.6 },
          reason: { overall: 79.9, sel: 79.8, tsr: 73.6, agg: 86.4 } }
      ]
    },

    generator: {
      tabLabel: 'Image generators (OpenClaw + RPR fixed)',
      metaHeaders: ['Name', 'Type', 'Controller'],
      desc:
        'Image-generator comparison on the same 90-case <b>LongBanana</b> benchmark with OpenClaw + RPR fixed as the controller workflow. ' +
        'Columns mirror the strategy table. ' +
        '<b>Metric note:</b> All models use unweighted checklist-average scores (0&ndash;100) for the subclass and Overall Avg. columns; suite averages are the mean of their three subclass scores. Only <b>P@70%</b> uses the difficulty-weighted task pass rate. ' +
        'The best value in each column is <b>in-bold</b>, the second best is <u>underlined</u>.',
      rows: [
        { info: { name: 'GPT Image 1', type: 'generator', typeLabel: 'Generator', backend: 'OpenClaw + RPR' },
          overall: { overall: 61.8, p70: 17.8 },
          topo: { overall: 50.2, scc: 54.3, rgc: 47.1, lac: 49.3 },
          appr: { overall: 76.2, gac: 94.0, lab: 87.2, ahc: 47.4 },
          reason: { overall: 58.9, sel: 54.0, tsr: 62.1, agg: 60.5 } },

        { info: { name: 'Seedream 4', type: 'generator', typeLabel: 'Generator', backend: 'OpenClaw + RPR' },
          overall: { overall: 63.6, p70: 18.9 },
          topo: { overall: 54.6, scc: 60.0, rgc: 52.6, lac: 51.2 },
          appr: { overall: 73.6, gac: 92.3, lab: 82.0, ahc: 46.6 },
          reason: { overall: 62.5, sel: 50.9, tsr: 67.8, agg: 68.7 } },

        { info: { name: 'Nano Banana 2', type: 'generator', typeLabel: 'Generator', backend: 'OpenClaw + RPR' },
          overall: { overall: 78.4, p70: 47.8 },
          topo: { overall: 68.2, scc: 76.1, rgc: 64.5, lac: 64.1 },
          appr: { overall: 87.1, gac: 97.1, lab: 88.6, ahc: 75.6 },
          reason: { overall: 79.9, sel: 79.8, tsr: 73.6, agg: 86.4 } }
      ]
    }
  }
};

// ----- benchmark metadata for the charts + case sections -----
// Source: paper-longbanana_arxiv  ->  tables/task_taxonomy.tex, sec/3_benchmark.tex, sec/X_suppl.tex
window.LB.meta = {
  // headline statistics (Tab. dataset_stats + sec 3.1 + sec 5)
  stats: [
    { value: '90',     label: 'Cases',            sub: '3 suites &times; 9 subclasses &times; 10' },
    { value: '~32',    label: 'References / case', sub: 'heterogeneous reference set' },
    { value: '20+',    label: 'Constraints / case', sub: 'cross-reference' },
    { value: '4,670',  label: 'Atomic checklist tasks', sub: '51.9 per case (mean)' },
    { value: '46,700', label: 'Human-reviewed labels', sub: '900 outputs across 10 conditions' },
    { value: '0.83',   label: 'Inter-annotator &kappa;', sub: '89.4% exact agreement' }
  ],

  // 3x3 taxonomy (10 cases per subclass). suite color families match the charts.
  taxonomy: [
    { suite: 'Scene Composition', color: '#2a72d6', shades: ['#2a72d6', '#5b94e0', '#8bb6ea'],
      subclasses: [
        { code: 'SCC', name: 'Semantic Coverage & Consistency', count: 10 },
        { code: 'RGC', name: 'Relational Graph Consistency', count: 10 },
        { code: 'LAC', name: 'Layout Arrangement Consistency', count: 10 }
      ] },
    { suite: 'Visual Appearance', color: '#16a085', shades: ['#16a085', '#3fb89e', '#71ccb8'],
      subclasses: [
        { code: 'GAC', name: 'Global Appearance Conditioning', count: 10 },
        { code: 'LAB', name: 'Local Appearance Binding', count: 10 },
        { code: 'AHC', name: 'Appearance Harmonization & Coherence', count: 10 }
      ] },
    { suite: 'Reference Reasoning', color: '#e08a1e', shades: ['#e08a1e', '#e8a44d', '#efbd7d'],
      subclasses: [
        { code: 'SEL', name: 'Selection & Retrieval', count: 10 },
        { code: 'TSR', name: 'Temporal / State Reasoning', count: 10 },
        { code: 'AGG', name: 'Counting & Aggregation', count: 10 }
      ] }
  ],

  // real benchmark case examples (sec X_suppl, Figs 7-16: per-case input + eval checklist).
  // Each `input` figure shows the reference set, target instruction and a representative output;
  // `evalImg` shows the partial evaluation checklist for that case.
  cases: [
    { id: 'RGC-001', suite: 'Scene Composition', subclass: 'Relational Graph Consistency',
      dimension: 'Relational Binding',
      input: 'assets/case_rgc_input_1600.jpg?v=1', evalImg: 'assets/case_rgc_eval_1600.jpg?v=1' },
    { id: 'LAC-002', suite: 'Scene Composition', subclass: 'Layout Arrangement Consistency',
      dimension: 'Global Constraint Satisfaction',
      input: 'assets/case_lac_input_1600.jpg?v=1', evalImg: 'assets/case_lac_eval_1600.jpg?v=1' },
    { id: 'LAB-007', suite: 'Visual Appearance', subclass: 'Local Appearance Binding',
      dimension: 'Relational Binding',
      input: 'assets/case_lab_input_1600.jpg?v=1', evalImg: 'assets/case_lab_eval_1600.jpg?v=1' },
    { id: 'TSR-008', suite: 'Reference Reasoning', subclass: 'Temporal / State Reasoning',
      dimension: 'Global Constraint Satisfaction',
      input: 'assets/case_tsr_input_1600.jpg?v=1', evalImg: 'assets/case_tsr_eval_1600.jpg?v=1' },
    { id: 'AGG-004', suite: 'Reference Reasoning', subclass: 'Counting & Aggregation',
      dimension: 'Global Constraint Satisfaction',
      input: 'assets/case_agg_input_1600.jpg?v=1', evalImg: 'assets/case_agg_eval_1600.jpg?v=1' }
  ],

  // Checklist-average generator scores (0-100), OpenClaw + RPR fixed as controller.
  // Source: tables/generator_comparison_tables.tex (tab:generator_comparison_openclaw),
  // converted from the original 0-10 scale (x10). Used so the radar charts share ONE metric
  // (checklist-average) instead of mixing in the difficulty-weighted generator numbers.
  generatorCA: [
    { info: { name: 'Nano Banana 2' },
      overall: { overall: 78.4 },
      topo: { scc: 76.1, rgc: 64.5, lac: 64.1 },
      appr: { gac: 97.1, lab: 88.6, ahc: 75.6 },
      reason: { sel: 79.8, tsr: 73.6, agg: 86.4 } },
    { info: { name: 'Seedream 4' },
      overall: { overall: 63.6 },
      topo: { scc: 60.0, rgc: 52.6, lac: 51.2 },
      appr: { gac: 92.3, lab: 82.0, ahc: 46.6 },
      reason: { sel: 50.9, tsr: 67.8, agg: 68.7 } },
    { info: { name: 'GPT Image 1' },
      overall: { overall: 61.8 },
      topo: { scc: 54.3, rgc: 47.1, lac: 49.3 },
      appr: { gac: 94.0, lab: 87.2, ahc: 47.4 },
      reason: { sel: 54.0, tsr: 62.1, agg: 60.5 } }
  ]
};
