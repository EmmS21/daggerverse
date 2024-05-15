/**
 * Module: CreateSvelteTests
 *
 * This Dagger module automates the process of creating unit tests for SvelteKit projects
 * using AI through Langchain to chain a process that generates suggestions for unit tests iteratively
 * based on best practices. The Langchain ConversationChain then generates unit tests based on the suggestions made.
 * This code is written into a file that is exported and returned when a user runs this method
 * 
 * Function: generateUnitTests
 * 
 * Description:
 * The generateUnitTests function uses LangChain to create a conversational chat 
 * that generates suggestions for unit tests twice. 
 * This approach ensures the suggestions meet best practices and allows for refinement
 * based on previous responses. The function then generates unit tests based on these 
 * refined suggestions, writes the tests to a file, and outputs the test file.
 * 
 * Args:
 * - root (dagger.Directory): The root directory of the Sveltekit project
 * - folder (string): The folder containing the Sveltekit component
 * - filename (string): The filename of the Sveltekit component
 * - token (Secret): A secret token required for authenticating with OpenAI
 * 
 * Returns:
 * File: A file containing the generated unit tests
 * 
 * Private Functions
 * 
 * Function: checkExists ->
 * Descritption: 
 * This function verifies the existence of a specified path within the container. 
 * If the path does not exist, it throws an error with detailed information about the directory structure 
 * or files present in the directory.
 * 
 * Args:
 * - container (Container): The Dagger container
 * - path (string): The path to check
 * - errorMessage (string): The error message to throw if the path does not exist
 * - extraInfo (string): Additional information to include in the error message
 * 
 * Returns:
 * None, but throws an error if the path does not exist.
 * 
 * Function: analyzeSvelteComponent ->
 * Description:
 * This function analyzes the provided Svelte component code and generates suggestions for unit tests 
 * using LangChain. It iteratively refines these suggestions to ensure they meet best practices.
 * 
 * Args:
 * - content (string): The content of the Sveltekit component
 * - apiKey (string): The OpenAI API key
 * - filePath (string): The path to the Svelte component file
 * - dirStructure (string): The directory structure of the project
 * - container (Container): The Dagger container
 * 
 * Returns:
 * string: The final unit test code to be written to a file
 * 
 * Function: generateOutput ->
 * Description:
 * This function generates output from LangChain based on the provided system and human prompts.
 * It uses a conversational chain to refine the suggestions for unit tests iteratively.
 * 
 * Args:
 * - apiKey (string): The OpenAI API key
 * - systemPrompt (string): The system prompt to provide context for the AI
 * - humanPrompt (string): The human prompt to request specific output from the AI
 * 
 * Returns:
 * string: The genereated output from LangChain
 * 
 * Function: writeCodeToFile ->
 * Description:
 * This function writes the generated unit test code to a file within the container. 
 * It extracts the TypeScript code block from the AI's response and 
 * ensures it is correctly formatted and written to the file.
 * 
 * Args:
 * - content (string): The content to write to the file
 * - container (Container): The Dagger containe
 * 
 * Returns:
 * string: The path to the written test file
 * 
 * Example Call:
 * - dagger call generateUnitTests --root='../src' --folder:'routes' --filename='+page.svelte' --token=env:OPENAI  export --path=/Users/test123 
 */

import { dag, Container, Directory, object, func, Secret } from "@dagger.io/dagger"
import { ChatOpenAI } from "langchain/chat_models/openai";
import { SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate, MessagesPlaceholder } from "langchain/prompts";
import { ConversationChain } from "langchain/chains";
import { BufferMemory } from "langchain/memory";
import util from 'util';
import { exec } from 'child_process';


@object()
// eslint-disable-next-line @typescript-eslint/no-unused-vars
class CreateSvelteTests {
  execPromise = util.promisify(exec);
  static historyPlaceholder: MessagesPlaceholder = new MessagesPlaceholder("history");
  static memory: BufferMemory = new BufferMemory({ returnMessages: true, memoryKey: "history" });

  @func()
  /** 
    Generates unit tests for Sveltekit projects based on the provided Svelte component code, folder structure, and file paths.

    Args:
      root (dagger.Directory): The root directory of the Svelte project.
    - folder (str): The folder containing the Svelte component.
    - filename (str): The filename of the Svelte component.
    - token (Secret): A secret token required for authentication.

    Returns:
    Directory: A directory containing the generated unit test files.
  */
  async generateUnitTests(root: Directory, folder: string, filename: string, token: Secret): Promise<Directory>{  
    const plainTextApiKey = await token.plaintext()
    const tempDir = root.withNewDirectory("/src/tests", { permissions: 0o777 });
    const container = dag.container()
      .from("alpine:latest")
      .withMountedDirectory("/mnt", tempDir)
      .withWorkdir("/mnt")

    const dirStructure = await container.withExec(["tree", "/mnt/src"]).stdout()

    try {
      const folderPath = `/mnt/src/${folder}`;
      await this.checkExists(container, folderPath, `Folder ${folder} not found`, dirStructure);

      const filePath = `${folderPath}/${filename}`;
      await this.checkExists(container, filePath, `File: ${filename} not found`, folderPath);

      const content = await container
        .withExec(["cat", filePath])
        .stdout();
      if(!content){
        throw new Error("File is empty or cannot be read");
      }
      
      const resultFile = await this.analyzeSvelteComponent(content, plainTextApiKey, filePath, dirStructure, container)
      const finalRes =  resultFile
    
      const newTestFile = tempDir.withNewFile("/tests/Home.test.ts", finalRes)

      return newTestFile.directory('/tests')

    } catch (error){
        throw new Error(`Error: ${error.message}`);
      }
  }
  /**  
    Custom error handling
  */
 private async checkExists(container: Container, path: string, errorMessage: string, extraInfo: string) {
  try {
    await container.withExec(["ls", "-la", path]).stdout();
  } catch (error) {
      if(path.includes('.')) {
        const folderPath = path.substring(0, path.lastIndexOf('/'));
        const output = await container.withExec(["ls", "-la", folderPath]).stdout();
        const filesList = output.split('\n').filter(line => !line.startsWith('total')).join('\n');
        throw new Error(`${errorMessage}. Files in directory:\n${filesList}`);
      } else {
        throw new Error(`${errorMessage}. Project structure:\n${extraInfo}`);
      }
  }
 }
  /** 
    Analyses code and returns unit test suggestions
  */
  private async analyzeSvelteComponent(content: string, 
      apiKey: string, 
      filePath: string, 
      dirStructure: string, 
      container: Container): 
    Promise<string>{
    let systemPrompt = "Analyze the provided Svelte component code and suggest what unit tests should be written."
    let humanPrompt = `Generate suggestions for unit tests for my Sveltekit project ${content}`;
    let response = await this.generateOutput(apiKey, systemPrompt, humanPrompt);
    
    for(let i = 0; i < 1; i++) {
      humanPrompt = `Refine unit test suggestions if necessary. Aim for simplicity and best practices in creating unit tests. Add more tests if necessary`;
      response = await this.generateOutput(apiKey, systemPrompt, humanPrompt)
    }

    systemPrompt = `Based on the accepted test suggestions, provide the full implementation code for these tests using Vitest. Include detailed assertions to comprehensively validate the component behaviors. Use the data-testid to identify elements. Include necessary imports for the tests. This is the location of the page being tested, ensure the import statement is named appropriately ${filePath}. Assume the location of the test code you are writing is in the folder tests. This is the structure of my project: ${dirStructure}, use this context to ensure the component is correctly imported, keeping in mind how to appropriately import components in Sveltekit based on relative paths. Keep in mind that describe, it, expect, beforeEach are all imported from vitest. Include these imports if they are used and prioritize using methods available in vitest where possible. If mocking functions is necessary, do not use Jest, use vitest`;
    humanPrompt = "Provide the full detailed code for the unit tests suggested now.";
    response = await this.generateOutput(apiKey, systemPrompt, humanPrompt)

    systemPrompt = 'You are a Typescript expert, your role is to ensure type annotations are included accurately in all code. Use appropriate descriptive types. Make no other changes other than this, aside from ensuring all assertions are included. If any assertions are missing, add these assertions';
    humanPrompt = "Include type annotations for the tests in the previous code. Ensure to return the full code with only these changes."
    response = await this.generateOutput(apiKey, systemPrompt, humanPrompt)
    return this.writeCodeToFile(response, container)
  }
  /**  
    This function will generate suggestions for unit tests based on both the code being tested and user feedback
  */
  private async generateOutput(apiKey: string, systemPrompt: string, humanPrompt: string): Promise<string> {
    try {
      const model = new ChatOpenAI({ openAIApiKey: apiKey, temperature: 0 });
      let inputTemplate = "{input}";
      let promptTemplates = [
        SystemMessagePromptTemplate.fromTemplate(systemPrompt),
        CreateSvelteTests.historyPlaceholder,
        HumanMessagePromptTemplate.fromTemplate(inputTemplate)
      ];
      const chain = new ConversationChain({
        memory: CreateSvelteTests.memory,
        prompt: ChatPromptTemplate.fromMessages(promptTemplates),
        llm: model,
      });
      const result = await chain.call({ input: humanPrompt });
      if (!result || !result.response || typeof result.response !== 'string') {
        throw new Error('Failed to obtain a valid string response', result);
      }
      return result.response; 
    } catch (error) {
        throw new Error(`OpenAI :${error.message}`)
    }
  }
  /** 
    Write unit tests and echo output
  */
  private async writeCodeToFile(content: string, container: Container): Promise<string> {
    let codeExtract = content.match(/```typescript([\s\S]*?)```/);
    if (!codeExtract || codeExtract.length < 2) {
      throw new Error("TypeScript code block not found in the response.");
    }
    const codeToWrite = codeExtract[1].trim();
    try {
      const writeTestsToFile = container
        .withExec([
          "sh",
          "-c",
          `printf "%b" "${codeToWrite.replace(/"/g, '\\"')}" > Home.test.ts && cat Home.test.ts`
        ]).stdout();
      return writeTestsToFile;
    } catch (error){
      throw new Error(`Error writing to file: ${error.message}`);
    };
  };
}
