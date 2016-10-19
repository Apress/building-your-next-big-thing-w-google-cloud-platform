/*
 * Copyright (C) 2015 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package com.lunchmates;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptions;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.Count;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.PTransform;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.SerializableComparator;
import com.google.cloud.dataflow.sdk.transforms.Top;
import com.google.cloud.dataflow.sdk.values.KV;
import com.google.cloud.dataflow.sdk.values.PCollection;

/**
 * This example extracts the most common response code occurrences from a typical HTTP log file using Cloud
 * Dataflow. It does so, by applying PTransforms to the selected data (a log file) referenced using the --input
 * parameter. In this routine, as you can see in @{link AllowedOptions}, if the input is not specified,
 * gs://lunchmates_logs/access.log is used as a default value. The default value for the output is also
 * specified: gs://lunchmates_logs/output/results.txt
 * <p> To execute this job locally, use the DirectPipelineRunner:
 * --runner=DirectPipelineRunner
 * --project=&lt;PROJECT ID&gt;
 * and specify an output file to store the results:
 * --output=[&lt;LOCAL FILE&gt; | gs://&lt;OUTPUT PREFIX&gt; | &lt;OTHER DATA SINK&gt;]
 * <p> To execute this pipeline using the Dataflow service, use one of the DataflowPipelineRunner or
 * BlockingDataflowPipelineRunner runners (async- or synchronous respectively). You must also specify a
 * --stagingLocation used to place temporary and and build files that the system needs to execute your pipeline:
 * --runner=[DataflowPipelineRunner | BlockingDataflowPipelineRunner]
 * --project=&lt;PROJECT ID&gt;
 * --stagingLocation=gs://&lt;STAGING DIRECTORY&gt;
 * and specify an output file to store the results:
 * --output=[gs://&lt;OUTPUT PREFIX&gt; | &lt;OTHER DATA SINK&gt;]
 */
public class LogAnalyzer {

    /**
     * Extracts the response codes for the attached logs.
     */
    private static class GetResponseCodeFn extends DoFn<String, String> {

        private static final long serialVersionUID = 523830295815285124L;

        private static final String RESPONSE_CODE_PATTERN = "HTTP[0-9./]{2,6}\" ([2345][0-9][0-9])";
        private static final Pattern pattern = Pattern.compile(RESPONSE_CODE_PATTERN);

        @Override
        public void processElement(ProcessContext context) {

            //  Find matches for the specified regular expression
            Matcher matcher = pattern.matcher(context.element());

            // Output each response code into the resulting PCollection
            if (matcher.find()) {
                context.output(matcher.group(1));
            }
        }
    }

    /**
     * Returns the top response codes in the logs
     */
    private static class TopCodes
            extends PTransform<PCollection<KV<String, Long>>, PCollection<List<KV<String, Long>>>> {

        private static final long serialVersionUID = 725379821789521L; // PTransform implements @{link Serializable}

        @Override
        public PCollection<List<KV<String, Long>>> apply(PCollection<KV<String, Long>> responseCodes) {

            return responseCodes.apply(Top.of(5, new SerializableComparator<KV<String, Long>>() {
                private static final long serialVersionUID = 23407910892310L;

                @Override
                public int compare(KV<String, Long> o1, KV<String, Long> o2) {
                    return Long.compare(o1.getValue(), o2.getValue());
                }
            }));
        }
    }

    /**
     * Converts a response code result into a string that can be processed by another routine.
     */
    private static class FormatResultsFn extends DoFn<List<KV<String, Long>>, String> {
        private static final long serialVersionUID = 8912558892015809521L;

        @Override
        public void processElement(ProcessContext context) {
            for (KV<String, Long> item : context.element()) {
                context.output(item.getKey() + "|" + item.getValue());
            }
        }
    }

    /**
     * This composite PTransform converts a PCollection containing lines of text into a PCollection with the top
     * five response codes in the HTTP log file used in the input.
     * Although this pipeline fragment could be inlined, bundling it as a PTransform allows for easy
     * reuse, modular testing, and an improved monitoring experience.
     */
    public static class ExtractLogExperience extends PTransform<PCollection<String>, PCollection<String>> {
        private static final long serialVersionUID = 9082135890251890235L;

        @Override
        public PCollection<String> apply(PCollection<String> lines) {

            // 1. Filter log line to extract response codes
            PCollection<String> responseCodes = lines.apply(ParDo.named("Extract Response Codes")
                                                                 .of(new GetResponseCodeFn()));

            // 2. Counts occurrences for each response code found
            PCollection<KV<String, Long>> responseCodeResults = responseCodes
                    .apply(Count.<String>perElement()
                                .withName("Count Response Codes"));

            // 3. Get the top five response codes
            PCollection<List<KV<String, Long>>> topThreeResponseCodes = responseCodeResults
                    .apply(new TopCodes()
                            .withName("Get Top Codes"));

            // 4. Format each word and count into a printable string.
            return topThreeResponseCodes.apply(ParDo.named("Format Output")
                                                    .of(new FormatResultsFn()));
        }
    }

    /**
     * Allowed set of options for this script
     */
    public interface AllowedOptions extends PipelineOptions {

        @Description("Default path to logs file")
        @Default.String("gs://lunchmates_logs/access.log")
        String getInput();

        void setInput(String value);

        @Description("Path to the file with the results")
        @Default.String("gs://lunchmates_logs/output/results.txt")
        String getOutput();

        void setOutput(String value);
    }

    public static void main(String[] args) {

        AllowedOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(AllowedOptions.class);
        Pipeline pipeline = Pipeline.create(options);

        pipeline.apply(TextIO.Read.named("Read Input").from(options.getInput()))
                .apply(new ExtractLogExperience().withName("Extract Logs UX"))
                .apply(TextIO.Write.named("Write Results")
                                   .to(options.getOutput())
                                   .withSuffix(".txt"));

        pipeline.run();
    }
}

