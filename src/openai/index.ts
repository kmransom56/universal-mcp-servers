import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import OpenAI from "openai";

export const openaiServer = new Server(
  {
    name: "multifamily-valuation/openai",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

// Initialize OpenAI client
let openai: OpenAI | null = null;

openaiServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "extractStructuredData",
        description: "Extract structured data from unstructured text using AI",
        inputSchema: {
          type: "object",
          properties: {
            text: {
              type: "string",
              description: "Unstructured text to extract data from",
            },
            schema: {
              type: "object",
              description: "JSON schema defining the structure of the data to extract",
            },
          },
          required: ["text", "schema"],
        },
      },
      {
        name: "analyzePropertyDocument",
        description: "Analyze property document text and extract key information",
        inputSchema: {
          type: "object",
          properties: {
            text: {
              type: "string",
              description: "Document text to analyze",
            },
            documentType: {
              type: "string",
              description: "Type of document (offeringMemorandum, rentRoll, or trailing12)",
              enum: ["offeringMemorandum", "rentRoll", "trailing12"],
            },
          },
          required: ["text", "documentType"],
        },
      },
      {
        name: "generatePropertyValuation",
        description: "Generate property valuation based on financial data",
        inputSchema: {
          type: "object",
          properties: {
            propertyData: {
              type: "object",
              description: "Property data including financial metrics",
            },
          },
          required: ["propertyData"],
        },
      },
      {
        name: "summarizePropertyInvestment",
        description: "Generate a summary of the property investment opportunity",
        inputSchema: {
          type: "object",
          properties: {
            propertyData: {
              type: "object",
              description: "Property data including financial metrics",
            },
            analysisResults: {
              type: "object",
              description: "Results of financial analysis",
            },
          },
          required: ["propertyData", "analysisResults"],
        },
      },
    ],
  };
});

openaiServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (!openai) {
    return {
      content: [
        {
          type: "text",
          text: "OpenAI client is not initialized. Please set OPENAI_API_KEY environment variable.",
        },
      ],
      isError: true,
    };
  }

  if (request.params.name === "extractStructuredData") {
    const text = request.params.arguments?.text as string;
    const schema = request.params.arguments?.schema as Record<string, any>;
    
    if (!text || !schema) {
      return {
        content: [{ type: "text", text: "Text and schema are required" }],
        isError: true,
      };
    }
    
    try {
      const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
          {
            role: "system",
            content: `You are a data extraction assistant. Extract structured data from the provided text according to the specified JSON schema. Return ONLY valid JSON that matches the schema.`,
          },
          {
            role: "user",
            content: `Extract structured data from the following text according to this JSON schema: ${JSON.stringify(schema)}\n\nText: ${text}`,
          },
        ],
        response_format: { type: "json_object" },
      });
      
      const result = response.choices[0]?.message?.content || "{}";
      
      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
        isError: false,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        content: [
          {
            type: "text",
            text: `Error extracting structured data: ${errorMessage}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "analyzePropertyDocument") {
    const text = request.params.arguments?.text as string;
    const documentType = request.params.arguments?.documentType as string;
    
    if (!text || !documentType) {
      return {
        content: [{ type: "text", text: "Text and document type are required" }],
        isError: true,
      };
    }
    
    try {
      let systemPrompt = "You are a real estate document analysis assistant. ";
      let schema: Record<string, any> = {};
      
      if (documentType === "offeringMemorandum") {
        systemPrompt += "Extract key information from the offering memorandum.";
        schema = {
          propertyName: "string",
          address: "string",
          city: "string",
          state: "string",
          zip: "string",
          purchasePrice: "number",
          capRate: "number",
          yearBuilt: "number",
          totalUnits: "number",
          propertyDescription: "string",
          highlights: ["string"],
          investmentSummary: "string",
        };
      } else if (documentType === "rentRoll") {
        systemPrompt += "Extract rent roll data from the document.";
        schema = {
          totalUnits: "number",
          occupiedUnits: "number",
          vacantUnits: "number",
          occupancyRate: "number",
          totalRent: "number",
          averageRent: "number",
          units: [
            {
              unitNumber: "string",
              unitType: "string",
              squareFeet: "number",
              rent: "number",
              occupied: "boolean",
            },
          ],
        };
      } else if (documentType === "trailing12") {
        systemPrompt += "Extract financial data from the trailing 12 months statement.";
        schema = {
          income: "number",
          expenses: "number",
          noi: "number",
          operatingExpenseRatio: "number",
          incomeBreakdown: {
            rentalIncome: "number",
            otherIncome: "number",
          },
          expenseBreakdown: {
            repairs: "number",
            maintenance: "number",
            taxes: "number",
            insurance: "number",
            utilities: "number",
            management: "number",
            administrative: "number",
            other: "number",
          },
        };
      }
      
      const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
          {
            role: "system",
            content: `${systemPrompt} Return ONLY valid JSON that matches the schema.`,
          },
          {
            role: "user",
            content: `Extract structured data from the following ${documentType} text. Return a JSON object with the extracted data.\n\nText: ${text.substring(0, 8000)}`,
          },
        ],
        response_format: { type: "json_object" },
      });
      
      const result = response.choices[0]?.message?.content || "{}";
      
      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
        isError: false,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        content: [
          {
            type: "text",
            text: `Error analyzing property document: ${errorMessage}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "generatePropertyValuation") {
    const propertyData = request.params.arguments?.propertyData as Record<string, any>;
    
    if (!propertyData) {
      return {
        content: [{ type: "text", text: "Property data is required" }],
        isError: true,
      };
    }
    
    try {
      const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
          {
            role: "system",
            content: `You are a real estate valuation expert. Generate a property valuation based on the provided financial data. Include multiple valuation methods (Cap Rate, GRM, DCF) and provide a final valuation range. Return the result as JSON.`,
          },
          {
            role: "user",
            content: `Generate a property valuation based on the following property data:\n\n${JSON.stringify(propertyData, null, 2)}`,
          },
        ],
        response_format: { type: "json_object" },
      });
      
      const result = response.choices[0]?.message?.content || "{}";
      
      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
        isError: false,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        content: [
          {
            type: "text",
            text: `Error generating property valuation: ${errorMessage}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "summarizePropertyInvestment") {
    const propertyData = request.params.arguments?.propertyData as Record<string, any>;
    const analysisResults = request.params.arguments?.analysisResults as Record<string, any>;
    
    if (!propertyData || !analysisResults) {
      return {
        content: [{ type: "text", text: "Property data and analysis results are required" }],
        isError: true,
      };
    }
    
    try {
      const response = await openai.chat.completions.create({
        model: "gpt-4",
        messages: [
          {
            role: "system",
            content: `You are a real estate investment advisor. Generate a comprehensive summary of the property investment opportunity based on the provided property data and analysis results. Include key metrics, strengths, weaknesses, and investment recommendations.`,
          },
          {
            role: "user",
            content: `Generate a summary of the property investment opportunity based on the following data:\n\nProperty Data: ${JSON.stringify(propertyData, null, 2)}\n\nAnalysis Results: ${JSON.stringify(analysisResults, null, 2)}`,
          },
        ],
      });
      
      const result = response.choices[0]?.message?.content || "";
      
      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
        isError: false,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        content: [
          {
            type: "text",
            text: `Error summarizing property investment: ${errorMessage}`,
          },
        ],
        isError: true,
      };
    }
  }
  
  throw new Error("Tool not found");
});

// Export a function to initialize the OpenAI MCP server
export function initializeOpenAIServer(apiKey: string) {
  openai = new OpenAI({ apiKey });
  return openaiServer;
}
