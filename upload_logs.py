import redis

# Connect to Redis Client
hostname = 'redis-19487.c8.us-east-1-4.ec2.redns.redis-cloud.com'
portnumber = 19487
password = 'ee3x3qAQ7yPMws3P5vHquvbE8o6LY84d'


r = redis.StrictRedis(host=hostname,
                      port=portnumber,
                      password=password)

# Simulated Logs
with open('simulated_logs.txt', 'r') as f:
    logs_text = f.read()

encoded_logs = logs_text.split('\n')

# Push into Redis database
r.lpush('attendance:logs', *encoded_logs)

