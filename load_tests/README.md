# Zygotrip Load Testing Suite (Locust)

Comprehensive load testing suite for Zygotrip platform using Locust. Tests hotel search, booking flows, operator dashboards, and system limits.

## Installation

```bash
pip install locust
# Or: pip install -r requirements.txt (includes locust==2.17.0)
```

## Quick Start

```bash
# Start Django development server (if not already running)
python manage.py runserver

# In another terminal, run basic load test
locust -f load_tests/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser.

## Test Scenarios

### 1. Basic Load Test (locustfile.py)

Default test with multiple user types:

```bash
# Interactive UI (default)
locust -f load_tests/locustfile.py --host=http://localhost:8000

# Headless mode with specific parameters
locust -f load_tests/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  -u 100 \
  -r 10 \
  -t 5m
```

**Parameters:**
- `-u 100`: 100 concurrent users
- `-r 10`: 10 users spawned per second
- `-t 5m`: Run for 5 minutes

**User Types:**
- **ZogotripCustomer** (weight: 10)
  - Browse hotels
  - Search with filters
  - View details
  - Attempt bookings

- **ZogotripBusOperator** (weight: 1)
  - View dashboard
  - Check bus details
  - View bookings

- **ZogotripCabOwner** (weight: 1)
  - View dashboard
  - Check cab details
  - Check availability

### 2. Advanced Scenarios (scenarios.py)

#### Stress Test - Identify Breaking Points

```bash
locust -f load_tests/scenarios.py:StressTestUser \
  --host=http://localhost:8000 \
  --headless \
  -u 50 \
  -r 50 \
  -t 2m
```

**What it tests:**
- Rapid sequential requests (10 hotel searches)
- Multiple detail page loads in quick succession
- System breaking point identification

#### Spike Test - Sudden Load Increase

```bash
locust -f load_tests/scenarios.py:SpikeTestUser \
  --host=http://localhost:8000 \
  --headless \
  -u 500 \
  -r 100 \
  -t 5m
```

**What it tests:**
- Sudden 500 user spike
- Behavior under unexpected load
- Autoscaling effectiveness

#### Endurance Test - Long Running Load

```bash
locust -f load_tests/scenarios.py:EnduranceTestUser \
  --host=http://localhost:8000 \
  --headless \
  -u 200 \
  -r 20 \
  -t 30m
```

**What it tests:**
- Sustained load over 30 minutes
- Memory leaks
- Connection pool issues
- Logging overhead

#### Cache Effectiveness Test

```bash
locust -f load_tests/scenarios.py:CacheTestUser \
  --host=http://localhost:8000 \
  --headless \
  -u 100 \
  -r 10 \
  -t 10m
```

**What it tests:**
- Cache hit rates with repeated searches
- Cache invalidation effectiveness
- Response times with vs without cache

#### Concurrent Edits Test

```bash
locust -f load_tests/scenarios.py:ConcurrentEditsUser \
  --host=http://localhost:8000 \
  --headless \
  -u 30 \
  -r 10 \
  -t 5m
```

**What it tests:**
- Race conditions in availability updates
- Atomic operation effectiveness
- Lock contention
- Data consistency

#### Booking Pipeline Test

```bash
locust -f load_tests/scenarios.py:BookingPipelineUser \
  --host=http://localhost:8000 \
  --headless \
  -u 50 \
  -r 5 \
  -t 10m
```

**What it tests:**
- Complete booking flow under load
- Multi-step request sequences
- Session handling

## Running Custom Tests

### Interactive UI Mode (Recommended for Development)

```bash
locust -f load_tests/locustfile.py \
  --host=http://localhost:8000
```

Steps:
1. Open http://localhost:8089
2. Enter:
   - **Number of users to simulate**: 100
   - **Spawn rate (users/sec)**: 10
   - **Host**: http://localhost:8000
3. Click "Start swarming"
4. Monitor in real-time:
   - Response times
   - Error rates
   - RPS (requests per second)
   - User types distribution

### Headless Mode (For CI/CD)

```bash
locust -f load_tests/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  -u 200 \
  -r 20 \
  --run-time 10m \
  --csv=results
```

Outputs results to `results_stats.csv` and `results_failures.csv`

## Performance Benchmarks

### Target Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Response Time (P50) | < 200ms | > 300ms | > 500ms |
| Response Time (P95) | < 500ms | > 1000ms | > 2000ms |
| Response Time (P99) | < 1000ms | > 2000ms | > 5000ms |
| Error Rate | < 0.5% | > 1% | > 5% |
| RPS | > 100 | < 50 | < 20 |
| CPU Usage | < 70% | > 80% | > 95% |

### Cache Effectiveness

Without cache:
- Hotel search: ~150-200ms
- Cache hit: ~10-30ms
- **Improvement**: 80-85%

### Database Connection Pool

- Optimal: 50 connections
- Max: 100 connections
- Monitor: `connection_count` metric

## Monitoring During Load Test

### Key Metrics to Watch

1. **Response Times**
   ```
   HTTP requests with OK (Status 200):
   - GET /hotels/ ✓
   - POST /booking/ ✓
   - GET /buses/dashboard/ ✓
   ```

2. **Failure Points**
   ```
   If P99 > 2000ms, likely:
   - Database connection exhaustion
   - Cache miss storms
   - Rate limiting triggered
   ```

3. **Error Types**
   - 429: Rate limit exceeded
   - 503: Service unavailable
   - Connection timeout: Resource exhaustion

## Debugging Failed Tests

### Check Logs

```bash
# Django logs
tail -f logs/zygotrip.log

# Access logs (structured JSON)
tail -f logs/access.log | jq .

# Celery worker logs
celery -A zygotrip_project worker -l debug
```

### Redis Status

```bash
redis-cli
> INFO
> DBSIZE
> KEYS "ratelimit:*"  # Check rate limit entries
> KEYS "hotel_search:*"  # Check cache keys
```

### Database Connections

```bash
# PostgreSQL (if using it)
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT count(*) FROM pg_stat_activity;"
```

## Recommended Test Plan

1. **Baseline** (10 users, 5 min)
   - Establish baseline response times
   - Verify all endpoints working

2. **Normal Load** (100 users, 10 min)
   - Test under expected daily load
   - Monitor cache effectiveness

3. **Peak Load** (500 users, 10 min)
   - Simulate peak hour traffic
   - Identify performance bottlenecks

4. **Stress Test** (1000+ users, 5 min)
   - Find breaking point
   - Determine max RPS

5. **Endurance** (300 users, 1 hour)
   - Identify memory leaks
   - Check connection pool stability

## Production Deployment Checklist

- [ ] Load test completed with > 500 users
- [ ] P99 response time < 1000ms
- [ ] Error rate < 0.5%
- [ ] Cache hit rate > 80% for searches
- [ ] Rate limiting tested and effective
- [ ] Database connections stable
- [ ] Redis connection pool stable
- [ ] Celery workers handling async tasks
- [ ] Structured logging capturing all events
- [ ] Monitoring/alerts configured

## Troubleshooting

### High Response Times

```bash
# Check database slow queries
tail -f logs/zygotrip.log | grep "duration"

# Check Redis latency
redis-cli --latency

# Check CPU/memory
top -p $(pgrep -f "runserver")
```

### Connection Errors

```bash
# Increase Django connection pool
# In settings.py DATABASES['default']['CONN_MAX_AGE']: 600

# Check Redis connection limits
redis-cli CONFIG GET maxclients
```

### Timeout Errors

```bash
# Increase Celery task timeout
# In settings.py: CELERY_TASK_TIME_LIMIT = 60 * 60

# Check for hanging requests
curl -v http://localhost:8000/hotels/ --max-time 10
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://locust.io/faq.html)
- [Django Performance Tips](https://docs.djangoproject.com/en/5.1/topics/performance/)
