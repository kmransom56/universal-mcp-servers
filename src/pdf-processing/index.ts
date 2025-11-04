import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import pdfParse from "pdf-parse";

export const pdfProcessingServer = new Server(
  {
    name: "multifamily-valuation/pdf-processing",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

pdfProcessingServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "extractTextFromPdf",
        description: "Extract text content from a PDF file",
        inputSchema: {
          type: "object",
          properties: {
            pdfBase64: {
              type: "string",
              description: "Base64-encoded PDF content",
            },
          },
          required: ["pdfBase64"],
        },
      },
      {
        name: "extractTablesFromPdf",
        description: "Extract tables from a PDF file with structured data",
        inputSchema: {
          type: "object",
          properties: {
            pdfBase64: {
              type: "string",
              description: "Base64-encoded PDF content",
            },
            pages: {
              type: "array",
              items: {
                type: "number",
              },
              description: "Specific pages to extract tables from (optional)",
            },
          },
          required: ["pdfBase64"],
        },
      },
      {
        name: "extractRentRollData",
        description: "Extract structured data from a rent roll PDF",
        inputSchema: {
          type: "object",
          properties: {
            pdfBase64: {
              type: "string",
              description: "Base64-encoded rent roll PDF content",
            },
          },
          required: ["pdfBase64"],
        },
      },
      {
        name: "extractOfferingMemorandumData",
        description: "Extract key information from an offering memorandum PDF",
        inputSchema: {
          type: "object",
          properties: {
            pdfBase64: {
              type: "string",
              description: "Base64-encoded offering memorandum PDF content",
            },
          },
          required: ["pdfBase64"],
        },
      },
    ],
  };
});

pdfProcessingServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "extractTextFromPdf") {
    const pdfBase64 = request.params.arguments?.pdfBase64 as string;
    if (!pdfBase64) {
      return {
        content: [{ type: "text", text: "PDF content is required" }],
        isError: true,
      };
    }
    
    try {
      const pdfBuffer = Buffer.from(pdfBase64, "base64");
      const pdfData = await pdfParse(pdfBuffer);
      
      return {
        content: [
          {
            type: "text",
            text: pdfData.text,
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting text from PDF: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "extractTablesFromPdf") {
    const pdfBase64 = request.params.arguments?.pdfBase64 as string;
    const pages = request.params.arguments?.pages as number[];
    
    if (!pdfBase64) {
      return {
        content: [{ type: "text", text: "PDF content is required" }],
        isError: true,
      };
    }
    
    try {
      const pdfBuffer = Buffer.from(pdfBase64, "base64");
      const pdfData = await pdfParse(pdfBuffer);
      
      // This is a simplified implementation. In a real-world scenario,
      // you would use a more sophisticated table extraction library
      // like tabula-js, pdf.js, or a custom algorithm to identify and extract tables.
      
      // For now, we'll use a simple heuristic to identify potential tables
      // by looking for lines with consistent spacing patterns
      const lines = pdfData.text.split('\n');
      const potentialTableLines = lines.filter(line => {
        // Look for lines with multiple spaces or tabs as column separators
        return line.trim().length > 0 && 
               (line.includes('  ') || line.includes('\t'));
      });
      
      // Group consecutive table lines together
      const tables = [];
      let currentTable = [];
      
      for (const line of potentialTableLines) {
        if (line.trim().length === 0 && currentTable.length > 0) {
          tables.push([...currentTable]);
          currentTable = [];
        } else if (line.trim().length > 0) {
          currentTable.push(line);
        }
      }
      
      if (currentTable.length > 0) {
        tables.push(currentTable);
      }
      
      return {
        content: [
          {
            type: "text",
            text: `Extracted ${tables.length} potential tables from PDF:\n\n${
              tables.map((table, i) => 
                `Table ${i + 1}:\n${table.join('\n')}`
              ).join('\n\n')
            }`,
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting tables from PDF: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "extractRentRollData") {
    const pdfBase64 = request.params.arguments?.pdfBase64 as string;
    
    if (!pdfBase64) {
      return {
        content: [{ type: "text", text: "PDF content is required" }],
        isError: true,
      };
    }
    
    try {
      const pdfBuffer = Buffer.from(pdfBase64, "base64");
      const pdfData = await pdfParse(pdfBuffer);
      
      // Extract rent roll data using pattern matching
      // This is a simplified implementation that looks for common patterns in rent rolls
      const text = pdfData.text;
      
      // Extract units
      const unitMatches = text.match(/Unit\s+(\d+)/gi) || [];
      const units = unitMatches.map(match => match.replace(/Unit\s+/i, '').trim());
      
      // Extract rents
      const rentMatches = text.match(/\$\s*[\d,]+\.?\d*/g) || [];
      const rents = rentMatches.map(match => match.replace(/\$\s*/, '').replace(/,/g, ''));
      
      // Extract unit types (1BR, 2BR, etc.)
      const unitTypeMatches = text.match(/\d+\s*BR|\d+\s*bed/gi) || [];
      const unitTypes = unitTypeMatches.map(match => match.trim());
      
      // Extract square footage
      const sqftMatches = text.match(/\d+\s*sq\.?\s*ft\.?|\d+\s*sf/gi) || [];
      const sqft = sqftMatches.map(match => match.replace(/sq\.?\s*ft\.?|sf/gi, '').trim());
      
      // Create structured data
      const structuredData = {
        totalUnits: units.length,
        units: units.slice(0, 20).map((unit, i) => ({
          unitNumber: unit,
          rent: i < rents.length ? rents[i] : null,
          unitType: i < unitTypes.length ? unitTypes[i] : null,
          squareFeet: i < sqft.length ? sqft[i] : null,
        })),
      };
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(structuredData, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting rent roll data: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "extractOfferingMemorandumData") {
    const pdfBase64 = request.params.arguments?.pdfBase64 as string;
    
    if (!pdfBase64) {
      return {
        content: [{ type: "text", text: "PDF content is required" }],
        isError: true,
      };
    }
    
    try {
      const pdfBuffer = Buffer.from(pdfBase64, "base64");
      const pdfData = await pdfParse(pdfBuffer);
      
      const text = pdfData.text;
      
      // Extract property name
      const propertyNameMatch = text.match(/property\s*name\s*:\s*([^\n]+)/i) || 
                               text.match(/([A-Za-z0-9\s]+)\s*apartments/i);
      const propertyName = propertyNameMatch ? propertyNameMatch[1].trim() : null;
      
      // Extract address
      const addressMatch = text.match(/address\s*:\s*([^\n]+)/i) ||
                          text.match(/located\s*at\s*([^\n]+)/i);
      const address = addressMatch ? addressMatch[1].trim() : null;
      
      // Extract price or asking price
      const priceMatch = text.match(/price\s*:\s*\$?\s*([\d,]+)/i) ||
                        text.match(/asking\s*price\s*:\s*\$?\s*([\d,]+)/i);
      const price = priceMatch ? priceMatch[1].replace(/,/g, '') : null;
      
      // Extract cap rate
      const capRateMatch = text.match(/cap\s*rate\s*:\s*([\d.]+)%/i);
      const capRate = capRateMatch ? parseFloat(capRateMatch[1]) : null;
      
      // Extract number of units
      const unitsMatch = text.match(/(\d+)\s*units/i) ||
                        text.match(/units\s*:\s*(\d+)/i);
      const units = unitsMatch ? parseInt(unitsMatch[1]) : null;
      
      // Extract year built
      const yearBuiltMatch = text.match(/year\s*built\s*:\s*(\d{4})/i) ||
                            text.match(/built\s*in\s*(\d{4})/i);
      const yearBuilt = yearBuiltMatch ? parseInt(yearBuiltMatch[1]) : null;
      
      // Create structured data
      const structuredData = {
        propertyName,
        address,
        price,
        capRate,
        units,
        yearBuilt,
      };
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(structuredData, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting offering memorandum data: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
  
  throw new Error("Tool not found");
});

// Export the PDF processing server
export function initializePdfProcessingServer() {
  return pdfProcessingServer;
}
