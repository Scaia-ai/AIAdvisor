package ai.scaia;/*
 *@created 06/06/2024- 08:12
 *@author neha
 */

import ai.scaia.azure.AzureBlobStorageService;
import ai.scaia.azure.OpenAiAzureClient;
import ai.scaia.result.ProcessingResult;
import ai.scaia.tika.TikaFileProcessor;
import lombok.extern.slf4j.Slf4j;

import java.io.File;
import java.util.List;

import static ai.scaia.config.Config.getQuestionsFromProperties;

@Slf4j
public class Processor {

    public static void main(String[] args) throws Exception {
        List<File> files = downloadAllFilesFromAzureBlob();
        processFiles(files);
        log.info("Success {}", ProcessingResult.successResults);
        log.info("Failures {}" , ProcessingResult.failureResults);
    }

    private static void processFiles(List<File> files) throws Exception {
        log.info("Processing  {} files", files.size());
        for (File file : files) {
            log.info("Processing file {}", file.getAbsolutePath());
            String fileContent = extractFileContent(file);
            String openAIResponse = removeJsonTag(callAzureOpenAIWithPrompt(fileContent));
            uploadResponse(openAIResponse, file);
        }
    }

    private static String removeJsonTag(String openAIResponse) {
        return openAIResponse.replace("```json", "").replace("```", "");
    }

    private static void uploadResponse(String openAIResponse, File file) {
        String filename = changeFileExtension(file.getName(), "txt");
        AzureBlobStorageService.uploadData(openAIResponse, filename);
    }

    private static String callAzureOpenAIWithPrompt(String fileContent) {
        List<String> questions = getQuestionsFromProperties();
        return OpenAiAzureClient.sendContentAndQuestionToAzureOpenAI(fileContent, questions);
    }

    private static String extractFileContent(File file) throws Exception {
        String fileContent = callTikaToExtractContent(file);
        saveExtractedContent(file.getName(), fileContent);
        return fileContent;
    }

    private static void saveExtractedContent(String fileName, String fileContent) {
        TikaFileProcessor.saveExtractedText(fileName, fileContent);
    }

    private static String callTikaToExtractContent(File file) throws Exception {
        return TikaFileProcessor.getText(file);
    }

    private static List<File> downloadAllFilesFromAzureBlob() {
        return AzureBlobStorageService.downloadData();
    }

    private static String changeFileExtension(String fileName, String newExtension) {
        int lastDotIndex = fileName.lastIndexOf('.');
        return (lastDotIndex != -1 ? fileName.substring(0, lastDotIndex) : fileName) + "." + newExtension;
    }
}
