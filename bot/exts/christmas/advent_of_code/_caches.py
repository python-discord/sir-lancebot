import async_rediscache

leaderboard_counts = async_rediscache.RedisCache(namespace="AOC_leaderboard_counts")
leaderboard_cache = async_rediscache.RedisCache(namespace="AOC_leaderboard_cache")
assigned_leaderboard = async_rediscache.RedisCache(namespace="AOC_assigned_leaderboard")
