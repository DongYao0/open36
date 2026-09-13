package top.hcode.hoj.util;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 判题线程池（阶段8.2 重写）
 *
 * 旧实现的问题（150 人比赛不可接受）：
 *   - 线程数=CPU 数（20 线程主机上 20 个并发编译互相抢 CPU）；
 *   - 队列 200×CPU；
 *   - DiscardOldestPolicy 队满静默丢弃最早任务 → 判题记录永远 Pending。
 *
 * 新规则：
 *   - 线程数：JUDGE_WORKERS 环境变量（默认 6，10核20线程主机的压测起点）；
 *   - 队列容量：JUDGE_QUEUE_CAPACITY（默认 300）；
 *   - 拒绝策略：不允许丢弃。队满时任务回退到提交线程执行（CallerRuns 语义，
 *     形成天然背压：judge 控制线程变慢 → Redis 队列消费变慢 → 上游排队），
 *     同时递增 rejected 计数并告警日志——绝不静默；
 *   - 暴露 active/queued/completed/rejected 指标（/version 端点透出）。
 */
public class ThreadPoolUtils {

    private static volatile ThreadPoolExecutor executorService;

    private static final AtomicLong rejectedCount = new AtomicLong();

    /** 队满后经 30s 等待成功入队的次数（背压生效证据） */
    private static final AtomicLong queueWaitCount = new AtomicLong();

    private ThreadPoolUtils() {
    }

    private static ThreadPoolExecutor createPool() {
        int workers = intEnv("JUDGE_WORKERS",
                intEnv("HOJ_JUDGE_WORKERS", 6));
        int queueCapacity = intEnv("JUDGE_QUEUE_CAPACITY", 300);

        ThreadFactory factory = r -> {
            Thread t = new Thread(r, "hoj-judge-worker");
            t.setDaemon(false);
            return t;
        };

        RejectedExecutionHandler neverDrop = (r, executor) -> {
            // 压测前置加固：队满时先阻塞排队 30s（不占判题并行度），
            // 仍失败才由提交线程执行一个任务作为最后阀门——
            // 任务绝不丢弃；提交线程占用有界（单任务自身有超时），
            // 且上游 MAX_TASK_NUM 已把并发 /judge 呼入限制在 6，
            // 最坏并行度 = 6 worker + 6 HTTP 线程，有上界。
            if (executor.isShutdown()) {
                rejectedCount.incrementAndGet();
                org.slf4j.LoggerFactory.getLogger(ThreadPoolUtils.class)
                        .error("判题线程池已关闭，任务无法执行（仅发生在停机窗口）");
                return;
            }
            try {
                boolean queued = executor.getQueue().offer(r, 30, TimeUnit.SECONDS);
                if (queued) {
                    queueWaitCount.incrementAndGet();
                    return;
                }
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
            }
            rejectedCount.incrementAndGet();
            org.slf4j.LoggerFactory.getLogger(ThreadPoolUtils.class)
                    .warn("判题队列等待30s仍满，退化为提交线程执行（任务不丢失）");
            r.run();
        };

        return new ThreadPoolExecutor(
                workers,
                workers,
                30L, TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(queueCapacity),
                factory,
                neverDrop);
    }

    private static int intEnv(String key, int defaultVal) {
        String v = System.getenv(key);
        if (v == null || v.isBlank()) {
            return defaultVal;
        }
        try {
            return Integer.parseInt(v.trim());
        } catch (NumberFormatException e) {
            return defaultVal;
        }
    }

    private static class PluginConfigHolder {
        private final static ThreadPoolUtils INSTANCE = new ThreadPoolUtils();
    }

    public static ThreadPoolUtils getInstance() {
        return PluginConfigHolder.INSTANCE;
    }

    public ExecutorService getThreadPool() {
        // 双重检查懒加载：保持旧单例调用方式，同时允许 env 生效
        if (executorService == null) {
            synchronized (ThreadPoolUtils.class) {
                if (executorService == null) {
                    executorService = createPool();
                }
            }
        }
        return executorService;
    }

    // ── 指标（阶段8.2：/version 与日志透出）──

    public static int getActiveCount() {
        ThreadPoolExecutor pool = (ThreadPoolExecutor) getInstance().getThreadPool();
        return pool.getActiveCount();
    }

    public static int getQueuedCount() {
        ThreadPoolExecutor pool = (ThreadPoolExecutor) getInstance().getThreadPool();
        return pool.getQueue().size();
    }

    public static long getCompletedCount() {
        ThreadPoolExecutor pool = (ThreadPoolExecutor) getInstance().getThreadPool();
        return pool.getCompletedTaskCount();
    }

    public static long getRejectedCount() {
        return rejectedCount.get();
    }

    public static long getQueueWaitCount() {
        return queueWaitCount.get();
    }

    public static int getPoolSize() {
        ThreadPoolExecutor pool = (ThreadPoolExecutor) getInstance().getThreadPool();
        return pool.getPoolSize();
    }
}
