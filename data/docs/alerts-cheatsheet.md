# Alerts Cheat Sheet

## High CPU Usage
**Alert**: CPU usage > 80% for 5 minutes
**Quick Check**:
- `top` or `htop` to see process list
- Check for runaway processes
- Review recent deployments

**Common Causes**:
- Infinite loops in application code
- Database query issues
- Resource-intensive background jobs

**Resolution**:
- Restart problematic services
- Scale up resources if needed
- Investigate root cause

## High Memory Usage
**Alert**: Memory usage > 85% for 5 minutes
**Quick Check**:
- `free -h` to see memory status
- Check for memory leaks
- Review swap usage

**Common Causes**:
- Memory leaks in applications
- Large file uploads
- Inefficient data structures

**Resolution**:
- Restart services with high memory usage
- Check for memory leaks
- Scale up memory if needed

## Disk Space
**Alert**: Disk usage > 90%
**Quick Check**:
- `df -h` to see disk usage
- `du -sh /*` to find large directories
- Check log file sizes

**Common Causes**:
- Large log files
- Temporary files not cleaned up
- Database growth

**Resolution**:
- Clean up old log files
- Remove temporary files
- Archive old data

## Database Connection Issues
**Alert**: Database connection errors > 10/minute
**Quick Check**:
- Database service status
- Connection pool usage
- Network connectivity

**Common Causes**:
- Database service down
- Connection pool exhaustion
- Network issues

**Resolution**:
- Restart database service
- Check connection pool settings
- Verify network connectivity

## API Response Time
**Alert**: 95th percentile response time > 2 seconds
**Quick Check**:
- Application performance metrics
- Database query performance
- External service dependencies

**Common Causes**:
- Slow database queries
- External API delays
- Resource constraints

**Resolution**:
- Optimize database queries
- Add caching where appropriate
- Scale up resources

## Error Rate
**Alert**: Error rate > 5% for 5 minutes
**Quick Check**:
- Application error logs
- Recent deployments
- External service status

**Common Causes**:
- Bug in recent deployment
- External service failures
- Configuration issues

**Resolution**:
- Rollback recent deployment if needed
- Check external service status
- Verify configuration

## Quick Commands

### System Health
```bash
# Check system resources
top
htop
free -h
df -h

# Check service status
systemctl status <service>
docker ps
docker stats

# Check logs
journalctl -u <service> -f
docker logs <container>
```

### Network
```bash
# Check connectivity
ping <host>
telnet <host> <port>
curl -I <url>

# Check network usage
netstat -tulpn
ss -tulpn
```

### Process Management
```bash
# Find processes
ps aux | grep <process>
pgrep <process>

# Kill processes
kill <pid>
pkill <process>
killall <process>
```

## Emergency Contacts
- **OnCall**: oncall@company.com
- **Database Team**: db-team@company.com
- **Infrastructure**: infra@company.com
- **Security**: security@company.com
