package top.hcode.hoj.judge;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import org.springframework.stereotype.Component;
import top.hcode.hoj.common.exception.SystemError;
import top.hcode.hoj.judge.entity.JudgeDTO;
import top.hcode.hoj.judge.entity.JudgeGlobalDTO;
import top.hcode.hoj.judge.entity.LanguageConfig;
import top.hcode.hoj.judge.task.*;
import top.hcode.hoj.pojo.dto.TestJudgeReq;
import top.hcode.hoj.pojo.dto.TestJudgeRes;
import top.hcode.hoj.pojo.entity.problem.Problem;
import top.hcode.hoj.util.Constants;
import top.hcode.hoj.util.JudgeUtils;
import top.hcode.hoj.util.ThreadPoolUtils;

import javax.annotation.Resource;
import java.io.File;
import java.util.*;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorCompletionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * @Author: Himit_ZH
 * @Date: 2021/4/16 12:15
 * @Description: 判题流程解耦重构3.0，该类负责输入数据进入程序进行测评
 */
@Component
public class JudgeRun {

    @Resource
    private DefaultJudge defaultJudge;

    @Resource
    private SpecialJudge specialJudge;

    @Resource
    private InteractiveJudge interactiveJudge;

    @Resource
    private TestJudge testJudge;

    @Resource
    private LanguageConfigLoader languageConfigLoader;

    public List<JSONObject> judgeAllCase(Long submitId,
                                         Problem problem,
                                         String judgeLanguage,
                                         String testCasesDir,
                                         JSONObject testCasesInfo,
                                         String userFileId,
                                         String userFileContent,
                                         Boolean getUserOutput,
                                         String judgeCaseMode)
            throws SystemError, ExecutionException, InterruptedException {

        if (testCasesInfo == null) {
            throw new SystemError("The evaluation data of the problem does not exist", null, null);
        }

        JSONArray testcaseList = (JSONArray) testCasesInfo.get("testCases");

        // 默认给题目限制时间+200ms用来测评
        Long testTime = (long) problem.getTimeLimit() + 200;

        Constants.JudgeMode judgeMode = Constants.JudgeMode.getJudgeMode(problem.getJudgeMode());

        if (judgeMode == null) {
            throw new RuntimeException("The judge mode of problem " + problem.getProblemId() + " error:" + problem.getJudgeMode());
        }

        // 用户输出的文件夹
        String runDir = Constants.JudgeDir.RUN_WORKPLACE_DIR.getContent() + "/" + submitId;

        LanguageConfig runConfig = languageConfigLoader.getLanguageConfigByName(judgeLanguage);
        LanguageConfig spjConfig = languageConfigLoader.getLanguageConfigByName("SPJ-" + problem.getSpjLanguage());
        LanguageConfig interactiveConfig = languageConfigLoader.getLanguageConfigByName("INTERACTIVE-" + problem.getSpjLanguage());

        final AbstractJudge abstractJudge = getAbstractJudge(judgeMode);

        JudgeGlobalDTO judgeGlobalDTO = JudgeGlobalDTO.builder()
                .problemId(problem.getId())
                .judgeMode(judgeMode)
                .userFileId(userFileId)
                .userFileContent(userFileContent)
                .runDir(runDir)
                .testTime(testTime)
                .maxMemory((long) problem.getMemoryLimit())
                .maxTime((long) problem.getTimeLimit())
                .maxStack(problem.getStackLimit())
                .testCaseInfo(testCasesInfo)
                .judgeExtraFiles(JudgeUtils.getProblemExtraFileMap(problem, "judge"))
                .runConfig(runConfig)
                .spjRunConfig(spjConfig)
                .interactiveRunConfig(interactiveConfig)
                .needUserOutputFile(getUserOutput)
                .removeEOLBlank(problem.getIsRemoveEndBlank())
                .isFileIO(problem.getIsFileIO())
                .ioReadFileName(problem.getIoReadFileName())
                .ioWriteFileName(problem.getIoWriteFileName())
                .build();


        // OI题的subtask最低分模式，则每个subtask组只要有一个case非AC 或者 percentage为 0.0则该组剩余评测点跳过，不再评测
        if (Constants.Contest.TYPE_OI.getCode().equals(problem.getType())
                && Constants.JudgeCaseMode.SUBTASK_LOWEST.getMode().equals(judgeCaseMode)) {
            return subtaskJudgeAllCase(testcaseList, testCasesDir, judgeGlobalDTO, abstractJudge);
        } else if (Constants.JudgeCaseMode.ERGODIC_WITHOUT_ERROR.getMode().equals(judgeCaseMode)){
            // 顺序评测测试点，遇到非AC就停止！
            return ergodicJudgeAllCase(testcaseList, testCasesDir, judgeGlobalDTO, abstractJudge);
        } else {
            return defaultJudgeAllCase(testcaseList, testCasesDir, judgeGlobalDTO, abstractJudge);
        }
    }

    /**
     * 默认会评测全部的测试点数据
     * @param testcaseList
     * @param testCasesDir
     * @param judgeGlobalDTO
     * @param abstractJudge
     * @return
     * @throws ExecutionException
     * @throws InterruptedException
     */
    private List<JSONObject> defaultJudgeAllCase(JSONArray testcaseList,
                                                 String testCasesDir,
                                                 JudgeGlobalDTO judgeGlobalDTO,
                                                 AbstractJudge abstractJudge) throws ExecutionException, InterruptedException {
        List<FutureTask<JSONObject>> futureTasks = new ArrayList<>();
        for (int index = 0; index < testcaseList.size(); index++) {
            JSONObject testcase = (JSONObject) testcaseList.get(index);
            // 将每个需要测试的线程任务加入任务列表中
            final int testCaseId = index + 1;
            // 输入文件名
            final String inputFileName = testcase.getStr("inputName");
            // 输出文件名
            final String outputFileName = testcase.getStr("outputName");
            // 题目数据的输入文件的路径
            final String testCaseInputPath = testCasesDir + "/" + inputFileName;
            // 题目数据的输出文件的路径
            final String testCaseOutputPath = testCasesDir + "/" + outputFileName;
            // 数据库表的测试样例id
            final Long caseId = testcase.getLong("caseId", null);
            // 该测试点的满分
            final Integer score = testcase.getInt("score", 0);
            // 该测试点的分组（用于subtask）
            final Integer groupNum = testcase.getInt("groupNum", 1);

            final Long maxOutputSize = Math.max(testcase.getLong("outputSize", 0L) * 2, 32 * 1024 * 1024L);

            JudgeDTO judgeDTO = JudgeDTO.builder()
                    .testCaseNum(testCaseId)
                    .testCaseInputFileName(inputFileName)
                    .testCaseInputPath(testCaseInputPath)
                    .testCaseOutputFileName(outputFileName)
                    .testCaseOutputPath(testCaseOutputPath)
                    .maxOutputSize(maxOutputSize)
                    .score(score)
                    .build();

            futureTasks.add(new FutureTask<>(() -> {
                JSONObject result = abstractJudge.judge(judgeDTO, judgeGlobalDTO);
                result.set("caseId", caseId);
                result.set("score", judgeDTO.getScore());
                result.set("inputFileName", judgeDTO.getTestCaseInputFileName());
                result.set("outputFileName", judgeDTO.getTestCaseOutputFileName());
                result.set("groupNum", groupNum);
                result.set("seq", testCaseId);
                return result;
            }));

        }
        return SubmitBatchTask2ThreadPool(futureTasks);
    }

    /**
     * 顺序评测，遇到非AC就停止评测
     * @param testcaseList
     * @param testCasesDir
     * @param judgeGlobalDTO
     * @param abstractJudge
     * @return
     * @throws ExecutionException
     * @throws InterruptedException
     */
    private List<JSONObject> ergodicJudgeAllCase(JSONArray testcaseList,
                                                 String testCasesDir,
                                                 JudgeGlobalDTO judgeGlobalDTO,
                                                 AbstractJudge abstractJudge) throws ExecutionException, InterruptedException {
        List<JSONObject> judgeResList = new ArrayList<>();
        for (int index = 0; index < testcaseList.size(); index++) {
            JSONObject testcase = (JSONObject) testcaseList.get(index);
            // 将每个需要测试的线程任务加入任务列表中
            final int testCaseId = index + 1;
            // 输入文件名
            final String inputFileName = testcase.getStr("inputName");
            // 输出文件名
            final String outputFileName = testcase.getStr("outputName");
            // 题目数据的输入文件的路径
            final String testCaseInputPath = testCasesDir + "/" + inputFileName;
            // 题目数据的输出文件的路径
            final String testCaseOutputPath = testCasesDir + "/" + outputFileName;
            // 数据库表的测试样例id
            final Long caseId = testcase.getLong("caseId", null);
            // 该测试点的满分
            final Integer score = testcase.getInt("score", 0);
            // 该测试点的分组（用于subtask）
            final Integer groupNum = testcase.getInt("groupNum", 1);

            final Long maxOutputSize = Math.max(testcase.getLong("outputSize", 0L) * 2, 32 * 1024 * 1024L);

            JudgeDTO judgeDTO = JudgeDTO.builder()
                    .testCaseNum(testCaseId)
                    .testCaseInputFileName(inputFileName)
                    .testCaseInputPath(testCaseInputPath)
                    .testCaseOutputFileName(outputFileName)
                    .testCaseOutputPath(testCaseOutputPath)
                    .maxOutputSize(maxOutputSize)
                    .score(score)
                    .build();

            JSONObject judgeRes = SubmitTask2ThreadPool(new FutureTask<>(() -> {
                JSONObject result = abstractJudge.judge(judgeDTO, judgeGlobalDTO);
                result.set("caseId", caseId);
                result.set("score", judgeDTO.getScore());
                result.set("inputFileName", judgeDTO.getTestCaseInputFileName());
                result.set("outputFileName", judgeDTO.getTestCaseOutputFileName());
                result.set("groupNum", groupNum);
                result.set("seq", judgeDTO.getTestCaseNum());
                return result;
            }));
            judgeResList.add(judgeRes);
            Integer status = judgeRes.getInt("status");
            if (!Constants.Judge.STATUS_ACCEPTED.getStatus().equals(status)){
                break;
            }
        }
        return judgeResList;
    }

    /**
     * 根据测试点的groupNum进行分组，每组按顺序评测，遇到非AC有评测点得分为0分，不再评测该组剩余的测试点
     * @param testcaseList
     * @param testCasesDir
     * @param judgeGlobalDTO
     * @param abstractJudge
     * @return
     * @throws ExecutionException
     * @throws InterruptedException
     */
    private List<JSONObject> subtaskJudgeAllCase(JSONArray testcaseList,
                                                 String testCasesDir,
                                                 JudgeGlobalDTO judgeGlobalDTO,
                                                 AbstractJudge abstractJudge) throws ExecutionException, InterruptedException {
        Map<Integer, List<JudgeDTO>> judgeDTOMap = new LinkedHashMap<>();
        for (int index = 0; index < testcaseList.size(); index++) {
            JSONObject testcase = (JSONObject) testcaseList.get(index);
            // 将每个需要测试的线程任务加入任务列表中
            final int testCaseId = index + 1;
            // 输入文件名
            final String inputFileName = testcase.getStr("inputName");
            // 输出文件名
            final String outputFileName = testcase.getStr("outputName");
            // 题目数据的输入文件的路径
            final String testCaseInputPath = testCasesDir + "/" + inputFileName;
            // 题目数据的输出文件的路径
            final String testCaseOutputPath = testCasesDir + "/" + outputFileName;
            // 数据库表的测试样例id
            final Long caseId = testcase.getLong("caseId", null);
            // 该测试点的满分
            final Integer score = testcase.getInt("score", 0);
            // 该测试点的分组（用于subtask）
            final Integer groupNum = testcase.getInt("groupNum", 1);

            final Long maxOutputSize = Math.max(testcase.getLong("outputSize", 0L) * 2, 32 * 1024 * 1024L);

            JudgeDTO judgeDTO = JudgeDTO.builder()
                    .testCaseNum(testCaseId)
                    .testCaseInputFileName(inputFileName)
                    .testCaseInputPath(testCaseInputPath)
                    .testCaseOutputFileName(outputFileName)
                    .testCaseOutputPath(testCaseOutputPath)
                    .maxOutputSize(maxOutputSize)
                    .score(score)
                    .problemCaseId(caseId)
                    .build();
            List<JudgeDTO> judgeDTOList = judgeDTOMap.get(groupNum);
            if (judgeDTOList == null) {
                judgeDTOList = new ArrayList<>();
                judgeDTOList.add(judgeDTO);
                judgeDTOMap.put(groupNum, judgeDTOList);
            } else {
                judgeDTOList.add(judgeDTO);
            }
        }

        List<JSONObject> judgeResList = new ArrayList<>();
        for (Map.Entry<Integer, List<JudgeDTO>> entry : judgeDTOMap.entrySet()) {
            Integer groupNum = entry.getKey();
            Iterator<JudgeDTO> iterator = entry.getValue().iterator();
            while (iterator.hasNext()) {
                JudgeDTO judgeDTO = iterator.next();
                JSONObject judgeRes = SubmitTask2ThreadPool(new FutureTask<>(() -> {
                    JSONObject result = abstractJudge.judge(judgeDTO, judgeGlobalDTO);
                    result.set("caseId", judgeDTO.getProblemCaseId());
                    result.set("score", judgeDTO.getScore());
                    result.set("inputFileName", judgeDTO.getTestCaseInputFileName());
                    result.set("outputFileName", judgeDTO.getTestCaseOutputFileName());
                    result.set("groupNum", groupNum);
                    result.set("seq", judgeDTO.getTestCaseNum());
                    return result;
                }));
                judgeResList.add(judgeRes);
                Integer status = judgeRes.getInt("status");
                Double percentage = judgeRes.getDouble("percentage");
                if (!Constants.Judge.STATUS_ACCEPTED.getStatus().equals(status)
                        && !(Constants.Judge.STATUS_PARTIAL_ACCEPTED.getStatus().equals(status)
                        && percentage != null && percentage > 0.0)) {
                    // 有评测点得分为0分，不再评测该组其他测试点
                    while (iterator.hasNext()) {
                        JudgeDTO elseJudgeDTO = iterator.next();
                        JSONObject elseJudgeRes = new JSONObject();
                        elseJudgeRes.set("status", Constants.Judge.STATUS_CANCELLED.getStatus());
                        elseJudgeRes.set("memory", 0);
                        elseJudgeRes.set("time", 0);
                        elseJudgeRes.set("errMsg", "Cancelled: Skipped Judging");
                        elseJudgeRes.set("caseId", elseJudgeDTO.getProblemCaseId());
                        elseJudgeRes.set("score", elseJudgeDTO.getScore());
                        elseJudgeRes.set("inputFileName", elseJudgeDTO.getTestCaseInputFileName());
                        elseJudgeRes.set("outputFileName", elseJudgeDTO.getTestCaseOutputFileName());
                        elseJudgeRes.set("groupNum", groupNum);
                        elseJudgeRes.set("seq", judgeDTO.getTestCaseNum());
                        judgeResList.add(elseJudgeRes);
                    }
                    break;
                }
            }
        }
        return judgeResList;
    }

    /**
     * 运行自测评测单个测试点（由接口传入 输入与输出的数据）
     * @param userFileId
     * @param testJudgeReq
     * @return
     * @throws ExecutionException
     * @throws InterruptedException
     */
    public TestJudgeRes testJudgeCase(String userFileId, TestJudgeReq testJudgeReq) throws ExecutionException, InterruptedException {

        // 默认给限制时间+200ms用来测评
        Long testTime = testJudgeReq.getTimeLimit() + 200L;

        LanguageConfig runConfig = languageConfigLoader.getLanguageConfigByName(testJudgeReq.getLanguage());

        JudgeGlobalDTO judgeGlobalDTO = JudgeGlobalDTO.builder()
                .judgeMode(Constants.JudgeMode.TEST)
                .userFileId(userFileId)
                .userFileContent(testJudgeReq.getCode())
                .testTime(testTime)
                .maxMemory((long) testJudgeReq.getMemoryLimit())
                .maxTime((long) testJudgeReq.getTimeLimit())
                .maxStack(testJudgeReq.getStackLimit())
                .removeEOLBlank(testJudgeReq.getIsRemoveEndBlank())
                .isFileIO(testJudgeReq.getIsFileIO())
                .ioReadFileName(testJudgeReq.getIoReadFileName())
                .ioWriteFileName(testJudgeReq.getIoWriteFileName())
                .runConfig(runConfig)
                .build();

        Long maxOutputSize = Math.max(testJudgeReq.getTestCaseInput().length() * 2L, 32 * 1024 * 1024L);

        JudgeDTO judgeDTO = JudgeDTO.builder()
                .testCaseInputContent(testJudgeReq.getTestCaseInput() + "\n")
                .maxOutputSize(maxOutputSize)
                .testCaseOutputContent(testJudgeReq.getExpectedOutput())
                .build();

        FutureTask<JSONObject> testJudgeFutureTask = new FutureTask<>(() -> testJudge.judge(judgeDTO, judgeGlobalDTO));

        JSONObject judgeRes = SubmitTask2ThreadPool(testJudgeFutureTask);
        return TestJudgeRes.builder()
                .status(judgeRes.getInt("status"))
                .memory(judgeRes.getLong("memory"))
                .time(judgeRes.getLong("time"))
                .stdout(judgeRes.getStr("output"))
                .stderr(judgeRes.getStr("errMsg"))
                .build();
    }

    private AbstractJudge getAbstractJudge(Constants.JudgeMode judgeMode) {
        switch (judgeMode) {
            case DEFAULT:
                return defaultJudge;
            case SPJ:
                return specialJudge;
            case INTERACTIVE:
                return interactiveJudge;
            default:
                throw new RuntimeException("The problem judge mode is error:" + judgeMode);
        }
    }

    /** 单任务（编译+全部用例）的保守超时包络 */
    private static final long SINGLE_TASK_TIMEOUT_SECONDS = 300;

    /** 批量任务（多用例并行）的整批超时包络 */
    private static final long BATCH_TIMEOUT_SECONDS = 600;

    /**
     * 提交单个判题任务并阻塞等待结果（阶段8.3）：
     * 旧实现每 10ms 轮询 isDone() 浪费线程与 CPU。
     * 现在 future.get(timeout) 直接阻塞；超时取消任务并返回系统错误，
     * InterruptedException 恢复中断标志后返回系统错误（不吞中断）。
     */
    private JSONObject SubmitTask2ThreadPool(FutureTask<JSONObject> futureTask)
            throws InterruptedException, ExecutionException {
        ThreadPoolUtils.getInstance().getThreadPool().submit(futureTask);
        try {
            return futureTask.get(SINGLE_TASK_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            futureTask.cancel(true);
            return busyResult("判题超时（单任务上限 " + SINGLE_TASK_TIMEOUT_SECONDS + "s）");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); // 恢复中断标志，交由上层决策
            return busyResult("判题被中断");
        }
    }

    /**
     * 批量提交并按完成顺序收集结果（阶段8.3）：
     * 用 ExecutorCompletionService 的 poll(timeout) 阻塞取代 10ms 轮询；
     * 整批设总超时，超时后取消未完成任务并返回系统错误。
     */
    private List<JSONObject> SubmitBatchTask2ThreadPool(List<FutureTask<JSONObject>> futureTasks)
            throws InterruptedException {
        ExecutorService pool = ThreadPoolUtils.getInstance().getThreadPool();
        ExecutorCompletionService<JSONObject> completion =
                new ExecutorCompletionService<>(pool);
        List<Future<JSONObject>> futures = new ArrayList<>(futureTasks.size());
        for (FutureTask<JSONObject> task : futureTasks) {
            futures.add(completion.submit(() -> {
                task.run();
                return task.get();
            }));
        }
        List<JSONObject> result = new LinkedList<>();
        long deadlineNanos = System.nanoTime()
                + TimeUnit.SECONDS.toNanos(BATCH_TIMEOUT_SECONDS);
        try {
            for (int i = 0; i < futureTasks.size(); i++) {
                long remaining = deadlineNanos - System.nanoTime();
                if (remaining <= 0) {
                    throw new TimeoutException();
                }
                Future<JSONObject> done = completion.poll(remaining, TimeUnit.NANOSECONDS);
                if (done == null) {
                    throw new TimeoutException();
                }
                result.add(done.get());
            }
        } catch (TimeoutException e) {
            for (Future<JSONObject> f : futures) {
                f.cancel(true);
            }
            result.clear();
            result.add(busyResult("批量判题超时（整批上限 " + BATCH_TIMEOUT_SECONDS + "s）"));
        } catch (ExecutionException e) {
            for (Future<JSONObject> f : futures) {
                f.cancel(true);
            }
            result.clear();
            String cause = e.getCause() != null ? e.getCause().getMessage() : e.getMessage();
            result.add(busyResult("判题执行异常: " + cause));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            result.clear();
            result.add(busyResult("批量判题被中断"));
        }
        return result;
    }

    /** 可识别的失败结果：状态=System Error，保留提交记录与错误信息（不丢任务） */
    private JSONObject busyResult(String message) {
        JSONObject res = new JSONObject();
        res.set("status", Constants.Judge.STATUS_SYSTEM_ERROR.getStatus());
        res.set("errMsg", message);
        res.set("time", 0);
        res.set("memory", 0);
        return res;
    }

}