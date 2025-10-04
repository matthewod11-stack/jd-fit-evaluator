# 🚀 JD-Fit Final Run - Optimized for 170+ Candidates

This optimized version provides significant performance improvements for processing your 170+ candidate final run.

## 🎯 Key Optimizations

### Performance Improvements
- **Parallel Processing**: Process candidates in parallel batches (8-12 workers)
- **Batch Optimization**: Intelligent batching to minimize API calls
- **Embedding Caching**: SQLite-based caching to avoid re-computing embeddings
- **Progress Monitoring**: Real-time progress tracking with Rich UI
- **Error Handling**: Robust error handling with detailed reporting

### Expected Performance
- **Original**: ~45-60 minutes for 170 candidates (sequential)
- **Optimized**: ~8-15 minutes for 170 candidates (parallel)
- **Speed Improvement**: 4-6x faster

## 🚀 Quick Start

### 1. Setup (One-time)
```bash
# Run the optimized setup
make setup-final-run

# Or manually:
./setup_final_run.sh
```

### 2. Configure OpenAI API Key
```bash
# Edit .env file and add your API key
export OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 3. Run Optimized Scoring
```bash
# Standard optimized run (8 workers, 32 batch size)
make final-run

# Or fast run (12 workers, 64 batch size) - for powerful machines
make final-run-fast

# Or custom configuration:
python optimized_final_run.py run-optimized \
  data/manifest.json \
  data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json \
  --workers 8 \
  --batch-size 32 \
  --out out
```

### 4. Monitor Progress
```bash
# Monitor in real-time
make monitor

# Or check health
make health
```

## 📊 Output Files

The optimized run creates the same output files as the original:
- `out/scores.json` - Complete scoring results
- `out/scores.csv` - CSV format for Excel/analysis
- `out/batch_summary.md` - Human-readable summary

## 🔧 Configuration Options

### Worker Configuration
- `--workers`: Number of parallel workers (default: 8)
  - **Conservative**: 4-6 workers
  - **Recommended**: 8 workers (M4 Max)
  - **Aggressive**: 12+ workers (for powerful machines)

### Batch Size
- `--batch-size`: Candidates per batch (default: 32)
  - **Small**: 16-24 (for slower networks)
  - **Standard**: 32-48
  - **Large**: 64+ (for fast networks)

### Example Configurations

**For M4 Max MacBook Pro (Recommended)**:
```bash
python optimized_final_run.py run-optimized \
  data/manifest.json \
  data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json \
  --workers 8 \
  --batch-size 32
```

**For Slower Network**:
```bash
python optimized_final_run.py run-optimized \
  data/manifest.json \
  data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json \
  --workers 4 \
  --batch-size 16
```

**For Fast Network + Powerful Machine**:
```bash
python optimized_final_run.py run-optimized \
  data/manifest.json \
  data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json \
  --workers 12 \
  --batch-size 64
```

## 🎛️ Environment Variables

Key environment variables for optimization:

```bash
# OpenAI Configuration
export JD_FIT_EMBEDDINGS__PROVIDER=openai
export JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-small
export JD_FIT_EMBEDDINGS__BATCH_SIZE=256
export JD_FIT_EMBEDDINGS__TIMEOUT_S=60

# API Key (Required)
export OPENAI_API_KEY=sk-your-actual-key-here

# Optional: LLM for Rationale
export JD_FIT_RATIONALE__PROVIDER=openai
export JD_FIT_RATIONALE__MODEL=gpt-4
```

## 📈 Performance Monitoring

### Real-time Progress
The optimized version shows:
- Progress bars with ETA
- Processing rate (candidates/second)
- Error counts and details
- Memory usage
- API call statistics

### Monitoring Commands
```bash
# Watch progress in real-time
make monitor

# Check system health
make health

# View detailed logs
tail -f out/batch_summary.md
```

## 🛠️ Troubleshooting

### Common Issues

**API Rate Limits**:
- Reduce `--workers` to 4-6
- Reduce `--batch-size` to 16-24
- Check your OpenAI rate limits

**Memory Issues**:
- Reduce `--workers` to 4-6
- Close other applications
- Monitor with `htop` or Activity Monitor

**Network Issues**:
- Reduce `--batch-size` to 16-24
- Increase `--timeout` if needed
- Check network connectivity

### Error Recovery
The optimized version includes robust error handling:
- Failed candidates are logged but don't stop the process
- Partial results are saved incrementally
- Detailed error reports in output

## 🔄 Migration from Original

If you're migrating from the original checklist:

1. **Replace the scoring command**:
   ```bash
   # Old way:
   python -m jd_fit_evaluator.cli score \
     --manifest data/manifest.json \
     --job_path data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json
   
   # New optimized way:
   make final-run
   ```

2. **Same output format**: All output files are identical
3. **Same UI**: Streamlit UI works unchanged
4. **Better performance**: 4-6x faster processing

## 📋 Pre-Run Checklist

Before running the optimized version:

- [ ] OpenAI API key configured
- [ ] Candidates folder exists (~/Desktop/Candidates)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`make setup-final-run`)
- [ ] Manifest created (automatic)
- [ ] Health check passed (`make health`)

## 🎯 Expected Results

With the optimized version, you should see:
- **Processing time**: 8-15 minutes (vs 45-60 minutes)
- **Success rate**: 95%+ candidates processed
- **Memory usage**: ~2-4GB peak
- **API calls**: Optimized batching reduces calls by 60-80%

## 🚀 Launch UI

After processing, launch the Streamlit UI:
```bash
make ui
# Then open http://localhost:8501
```

The UI works exactly the same as before, with all your optimized results!
