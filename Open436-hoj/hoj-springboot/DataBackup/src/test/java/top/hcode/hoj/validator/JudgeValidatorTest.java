package top.hcode.hoj.validator;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.hcode.hoj.common.exception.StatusFailException;
import top.hcode.hoj.pojo.dto.SubmitJudgeDTO;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

@ExtendWith(MockitoExtension.class)
class JudgeValidatorTest {

    @InjectMocks
    private JudgeValidator validator;

    @Mock
    private AccessValidator accessValidator;

    @Test
    void missingRemoteFlagDefaultsToLocalJudgeWithoutNullPointer() {
        SubmitJudgeDTO dto = validSubmission().setIsRemote(null);

        assertDoesNotThrow(() -> validator.validateSubmissionInfo(dto));
    }

    @Test
    void rejectsEmptyCodeWithBusinessError() {
        StatusFailException error = assertThrows(StatusFailException.class,
                () -> validator.validateSubmissionInfo(validSubmission().setCode("")));

        assertEquals("提交的代码不可为空！", error.getMessage());
    }

    @Test
    void rejectsEmptyLanguageWithBusinessError() {
        StatusFailException error = assertThrows(StatusFailException.class,
                () -> validator.validateSubmissionInfo(validSubmission().setLanguage(null)));

        assertEquals("提交的编程语言不可为空！", error.getMessage());
    }

    private SubmitJudgeDTO validSubmission() {
        return new SubmitJudgeDTO()
                .setPid("1000")
                .setCid(0L)
                .setLanguage("C++")
                .setCode("int main(){return 0;} // code length is deliberately longer than fifty characters");
    }
}
