import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as XLSX from "xlsx";

export const spreadsheetProcessingServer = new Server(
  {
    name: "multifamily-valuation/spreadsheet-processing",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

spreadsheetProcessingServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "parseExcelFile",
        description: "Parse an Excel file and extract all sheet data",
        inputSchema: {
          type: "object",
          properties: {
            excelBase64: {
              type: "string",
              description: "Base64-encoded Excel file content",
            },
          },
          required: ["excelBase64"],
        },
      },
      {
        name: "extractDataFromRange",
        description: "Extract data from a specific range in an Excel file",
        inputSchema: {
          type: "object",
          properties: {
            excelBase64: {
              type: "string",
              description: "Base64-encoded Excel file content",
            },
            sheet: {
              type: "string",
              description: "Sheet name to extract data from",
            },
            range: {
              type: "string",
              description: "Cell range in A1 notation (e.g., 'A1:C10')",
            },
          },
          required: ["excelBase64", "sheet", "range"],
        },
      },
      {
        name: "populateTemplate",
        description: "Populate an Excel template with data",
        inputSchema: {
          type: "object",
          properties: {
            templateBase64: {
              type: "string",
              description: "Base64-encoded Excel template file",
            },
            data: {
              type: "object",
              description: "Data to populate the template with (key-value pairs)",
            },
            cellMappings: {
              type: "object",
              description: "Mappings of data keys to cell references (e.g., { 'propertyName': 'B2' })",
            },
          },
          required: ["templateBase64", "data", "cellMappings"],
        },
      },
      {
        name: "extractFinancialData",
        description: "Extract financial metrics from trailing 12 data",
        inputSchema: {
          type: "object",
          properties: {
            excelBase64: {
              type: "string",
              description: "Base64-encoded Excel file content",
            },
          },
          required: ["excelBase64"],
        },
      },
      {
        name: "extractRentData",
        description: "Extract rent data from rent roll spreadsheet",
        inputSchema: {
          type: "object",
          properties: {
            excelBase64: {
              type: "string",
              description: "Base64-encoded Excel file content",
            },
          },
          required: ["excelBase64"],
        },
      },
      {
        name: "extractPropertyInfo",
        description: "Extract property information from offering memorandum",
        inputSchema: {
          type: "object",
          properties: {
            excelBase64: {
              type: "string",
              description: "Base64-encoded Excel file content",
            },
          },
          required: ["excelBase64"],
        },
      },
      {
        name: "generateAnalysisSpreadsheet",
        description: "Generate analysis spreadsheet based on property data",
        inputSchema: {
          type: "object",
          properties: {
            propertyData: {
              type: "object",
              description: "Property data to use for analysis",
            },
            templateName: {
              type: "string",
              description: "Template name to use for analysis",
              enum: [
                "Rental Property Analysis",
                "Fund IRR Calculator",
                "House Flipping Analysis",
                "Share Distribution"
              ]
            },
          },
          required: ["propertyData", "templateName"],
        },
      },
    ],
  };
});

spreadsheetProcessingServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "parseExcelFile") {
    const excelBase64 = request.params.arguments?.excelBase64 as string;
    
    if (!excelBase64) {
      return {
        content: [{ type: "text", text: "Excel file content is required" }],
        isError: true,
      };
    }
    
    try {
      const excelBuffer = Buffer.from(excelBase64, "base64");
      const workbook = XLSX.read(excelBuffer, { type: "buffer" });
      
      const result: { [key: string]: any } = {};
      workbook.SheetNames.forEach((sheetName: string) => {
        result[sheetName] = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);
      });
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error parsing Excel file: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "extractDataFromRange") {
    const excelBase64 = request.params.arguments?.excelBase64 as string;
    const sheet = request.params.arguments?.sheet as string;
    const range = request.params.arguments?.range as string;
    
    if (!excelBase64 || !sheet || !range) {
      return {
        content: [{ type: "text", text: "Excel file content, sheet name, and range are required" }],
        isError: true,
      };
    }
    
    try {
      const excelBuffer = Buffer.from(excelBase64, "base64");
      const workbook = XLSX.read(excelBuffer, { type: "buffer" });
      
      if (!workbook.SheetNames.includes(sheet)) {
        return {
          content: [{ type: "text", text: `Sheet '${sheet}' not found in workbook` }],
          isError: true,
        };
      }
      
      const worksheet = workbook.Sheets[sheet];
      const data = XLSX.utils.sheet_to_json(worksheet, { range });
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting data from range: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "populateTemplate") {
    const templateBase64 = request.params.arguments?.templateBase64 as string;
    const data = request.params.arguments?.data as Record<string, any>;
    const cellMappings = request.params.arguments?.cellMappings as Record<string, string>;
    
    if (!templateBase64 || !data || !cellMappings) {
      return {
        content: [{ type: "text", text: "Template file, data, and cell mappings are required" }],
        isError: true,
      };
    }
    
    try {
      const templateBuffer = Buffer.from(templateBase64, "base64");
      const workbook = XLSX.read(templateBuffer, { type: "buffer" });
      
      // Get the first sheet
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      
      // Populate the template with data
      Object.entries(cellMappings).forEach(([key, cellRef]) => {
        if (data[key] !== undefined) {
          worksheet[cellRef] = { v: data[key], t: typeof data[key] === 'number' ? 'n' : 's' };
        }
      });
      
      // Convert workbook to base64
      const outputBuffer = XLSX.write(workbook, { type: "buffer", bookType: "xlsx" });
      const outputBase64 = Buffer.from(outputBuffer).toString("base64");
      
      return {
        content: [
          {
            type: "text",
            text: `Template populated successfully. Base64 output:\n${outputBase64.substring(0, 100)}...`,
          },
          {
            type: "blob",
            mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            blob: outputBase64,
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error populating template: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "extractFinancialData") {
    const excelBase64 = request.params.arguments?.excelBase64 as string;
    
    if (!excelBase64) {
      return {
        content: [{ type: "text", text: "Excel file content is required" }],
        isError: true,
      };
    }
    
    try {
      const excelBuffer = Buffer.from(excelBase64, "base64");
      const workbook = XLSX.read(excelBuffer, { type: "buffer" });
      
      // Convert workbook to JSON
      const result: { [key: string]: any } = {};
      workbook.SheetNames.forEach((sheetName: string) => {
        result[sheetName] = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);
      });
      
      // Define keywords for income and expense categories
      const incomeKeywords = [
        'income', 'revenue', 'rent', 'total income', 'gross income', 
        'effective gross income', 'egi', 'receipts', 'collections',
        'other income', 'laundry', 'parking', 'storage', 'pet fees',
        'application fees', 'late fees', 'utility reimbursement',
        'rental income', 'miscellaneous income', 'amenity fees',
        'vending', 'interest income', 'forfeited deposits'
      ];
      
      const expenseKeywords = [
        'expense', 'expenses', 'cost', 'costs', 'operating expense',
        'operating expenses', 'opex', 'maintenance', 'repair', 'repairs',
        'utilities', 'utility', 'management', 'administrative', 'admin',
        'payroll', 'marketing', 'advertising', 'insurance', 'tax', 'taxes',
        'property tax', 'property taxes', 'legal', 'professional', 'contract',
        'landscaping', 'grounds', 'security', 'cleaning', 'janitorial',
        'supplies', 'replacement', 'turnover', 'bad debt', 'vacancy'
      ];
      
      // Extract financial metrics
      let income = 0;
      let expenses = 0;
      let noi = 0;
      
      // Process each sheet to find financial data
      Object.entries(result).forEach(([sheetName, sheetData]) => {
        // Skip empty sheets
        if (!Array.isArray(sheetData) || sheetData.length === 0) return;
        
        sheetData.forEach((row: any) => {
          // Convert row keys to lowercase for case-insensitive matching
          const rowEntries = Object.entries(row).map(([k, v]) => [k.toLowerCase(), v]);
          
          // Look for income items
          rowEntries.forEach(([key, value]) => {
            if (typeof key !== 'string') return;
            
            const keyStr = key.toLowerCase();
            if (incomeKeywords.some(keyword => keyStr.includes(keyword))) {
              // Check if value is a number or can be converted to one
              const numValue = typeof value === 'number' ? value : 
                              (typeof value === 'string' ? parseFloat(value.replace(/[$,]/g, '')) : NaN);
              
              if (!isNaN(numValue) && numValue > 0) {
                income += numValue;
              }
            }
            
            // Look for expense items
            if (expenseKeywords.some(keyword => keyStr.includes(keyword))) {
              // Check if value is a number or can be converted to one
              const numValue = typeof value === 'number' ? value : 
                              (typeof value === 'string' ? parseFloat(value.replace(/[$,]/g, '')) : NaN);
              
              if (!isNaN(numValue) && numValue > 0) {
                expenses += numValue;
              }
            }
          });
        });
      });
      
      // Calculate NOI
      noi = income - expenses;
      
      // Create financial data object
      const financialData = {
        income,
        expenses,
        noi,
        operatingExpenseRatio: expenses / income,
        capRate: noi / 1000000 * 100, // Placeholder cap rate calculation
      };
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(financialData, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting financial data: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "extractRentData") {
    const excelBase64 = request.params.arguments?.excelBase64 as string;
    
    if (!excelBase64) {
      return {
        content: [{ type: "text", text: "Excel file content is required" }],
        isError: true,
      };
    }
    
    try {
      const excelBuffer = Buffer.from(excelBase64, "base64");
      const workbook = XLSX.read(excelBuffer, { type: "buffer" });
      
      // Convert workbook to JSON
      const result: { [key: string]: any } = {};
      workbook.SheetNames.forEach((sheetName: string) => {
        result[sheetName] = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);
      });
      
      // Keywords to identify unit data
      const unitKeywords = ['unit', 'apt', 'apartment', 'number', 'unit number', 'unit #'];
      const rentKeywords = ['rent', 'monthly rent', 'current rent', 'rental rate'];
      const sizeKeywords = ['size', 'sq ft', 'sqft', 'square feet', 'area'];
      const typeKeywords = ['type', 'unit type', 'bed', 'bedroom', 'bath', 'bathroom', 'br', 'ba'];
      const occupancyKeywords = ['occupied', 'occupancy', 'vacant', 'vacancy', 'status'];
      
      // Extract rent data
      const units: any[] = [];
      let totalUnits = 0;
      let totalRent = 0;
      let totalOccupiedUnits = 0;
      let totalSquareFeet = 0;
      
      // Process each sheet to find unit data
      Object.entries(result).forEach(([sheetName, sheetData]) => {
        // Skip empty sheets
        if (!Array.isArray(sheetData) || sheetData.length === 0) return;
        
        // Find column headers that match our keywords
        const firstRow = sheetData[0];
        if (!firstRow) return;
        
        const headers = Object.keys(firstRow);
        
        // Map column headers to our data fields
        const unitColumn = headers.find(h => 
          unitKeywords.some(keyword => h.toLowerCase().includes(keyword))
        );
        
        const rentColumn = headers.find(h => 
          rentKeywords.some(keyword => h.toLowerCase().includes(keyword))
        );
        
        const sizeColumn = headers.find(h => 
          sizeKeywords.some(keyword => h.toLowerCase().includes(keyword))
        );
        
        const typeColumn = headers.find(h => 
          typeKeywords.some(keyword => h.toLowerCase().includes(keyword))
        );
        
        const occupancyColumn = headers.find(h => 
          occupancyKeywords.some(keyword => h.toLowerCase().includes(keyword))
        );
        
        // Extract unit data from each row
        sheetData.forEach((row: any) => {
          if (!row) return;
          
          const unitNumber = unitColumn ? row[unitColumn] : null;
          if (!unitNumber) return; // Skip rows without unit numbers
          
          // Extract rent value
          let rent = null;
          if (rentColumn && row[rentColumn] !== undefined) {
            const rentValue = row[rentColumn];
            rent = typeof rentValue === 'number' ? rentValue : 
                  (typeof rentValue === 'string' ? parseFloat(rentValue.replace(/[$,]/g, '')) : null);
          }
          
          // Extract size value
          let size = null;
          if (sizeColumn && row[sizeColumn] !== undefined) {
            const sizeValue = row[sizeColumn];
            size = typeof sizeValue === 'number' ? sizeValue : 
                  (typeof sizeValue === 'string' ? parseFloat(sizeValue.replace(/[,]/g, '')) : null);
          }
          
          // Extract unit type
          const unitType = typeColumn ? row[typeColumn] : null;
          
          // Extract occupancy status
          let occupied = null;
          if (occupancyColumn && row[occupancyColumn] !== undefined) {
            const occupancyValue = row[occupancyColumn];
            if (typeof occupancyValue === 'boolean') {
              occupied = occupancyValue;
            } else if (typeof occupancyValue === 'string') {
              occupied = !['vacant', 'vacancy', 'no', 'false', '0'].includes(occupancyValue.toLowerCase());
            } else if (typeof occupancyValue === 'number') {
              occupied = occupancyValue !== 0;
            }
          }
          
          // Add unit to the list
          units.push({
            unitNumber: String(unitNumber),
            rent: rent !== null ? rent : null,
            squareFeet: size !== null ? size : null,
            unitType: unitType !== null ? String(unitType) : null,
            occupied: occupied !== null ? occupied : true,
          });
          
          // Update totals
          totalUnits++;
          if (rent !== null) totalRent += rent;
          if (occupied !== null && occupied) totalOccupiedUnits++;
          if (size !== null) totalSquareFeet += size;
        });
      });
      
      // Calculate averages and metrics
      const occupancyRate = totalUnits > 0 ? (totalOccupiedUnits / totalUnits) * 100 : 0;
      const averageRent = totalUnits > 0 ? totalRent / totalUnits : 0;
      const averageRentPerSqFt = totalSquareFeet > 0 ? totalRent / totalSquareFeet : 0;
      
      // Create rent data object
      const rentData = {
        totalUnits,
        occupiedUnits: totalOccupiedUnits,
        vacantUnits: totalUnits - totalOccupiedUnits,
        occupancyRate,
        totalRent,
        averageRent,
        averageRentPerSqFt,
        units: units.slice(0, 20), // Limit to first 20 units for brevity
      };
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(rentData, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting rent data: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "extractPropertyInfo") {
    const excelBase64 = request.params.arguments?.excelBase64 as string;
    
    if (!excelBase64) {
      return {
        content: [{ type: "text", text: "Excel file content is required" }],
        isError: true,
      };
    }
    
    try {
      const excelBuffer = Buffer.from(excelBase64, "base64");
      const workbook = XLSX.read(excelBuffer, { type: "buffer" });
      
      // Convert workbook to JSON
      const result: { [key: string]: any } = {};
      workbook.SheetNames.forEach((sheetName: string) => {
        result[sheetName] = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);
      });
      
      // Keywords to identify property information
      const propertyNameKeywords = ['property name', 'property', 'name', 'asset'];
      const addressKeywords = ['address', 'location', 'property address'];
      const cityKeywords = ['city', 'municipality'];
      const stateKeywords = ['state', 'province'];
      const zipKeywords = ['zip', 'zip code', 'postal code', 'postal'];
      const priceKeywords = ['price', 'purchase price', 'asking price', 'sale price', 'value'];
      const capRateKeywords = ['cap rate', 'capitalization rate', 'cap'];
      const yearBuiltKeywords = ['year built', 'built', 'construction year'];
      
      // Extract property information
      let propertyName = null;
      let address = null;
      let city = null;
      let state = null;
      let zip = null;
      let price = null;
      let capRate = null;
      let yearBuilt = null;
      
      // Process each sheet to find property information
      Object.entries(result).forEach(([sheetName, sheetData]) => {
        // Skip empty sheets
        if (!Array.isArray(sheetData) || sheetData.length === 0) return;
        
        sheetData.forEach((row: any) => {
          // Convert row keys to lowercase for case-insensitive matching
          const rowEntries = Object.entries(row);
          
          rowEntries.forEach(([key, value]) => {
            if (typeof key !== 'string' || value === undefined || value === null) return;
            
            const keyStr = key.toLowerCase();
            
            // Extract property name
            if (propertyName === null && propertyNameKeywords.some(keyword => keyStr.includes(keyword))) {
              propertyName = String(value);
            }
            
            // Extract address
            if (address === null && addressKeywords.some(keyword => keyStr.includes(keyword))) {
              address = String(value);
            }
            
            // Extract city
            if (city === null && cityKeywords.some(keyword => keyStr.includes(keyword))) {
              city = String(value);
            }
            
            // Extract state
            if (state === null && stateKeywords.some(keyword => keyStr.includes(keyword))) {
              state = String(value);
            }
            
            // Extract zip
            if (zip === null && zipKeywords.some(keyword => keyStr.includes(keyword))) {
              zip = String(value);
            }
            
            // Extract price
            if (price === null && priceKeywords.some(keyword => keyStr.includes(keyword))) {
              if (typeof value === 'number') {
                price = value;
              } else if (typeof value === 'string') {
                const priceStr = value.replace(/[$,]/g, '');
                const parsedPrice = parseFloat(priceStr);
                if (!isNaN(parsedPrice)) {
                  price = parsedPrice;
                }
              }
            }
            
            // Extract cap rate
            if (capRate === null && capRateKeywords.some(keyword => keyStr.includes(keyword))) {
              if (typeof value === 'number') {
                capRate = value;
              } else if (typeof value === 'string') {
                const capRateStr = value.replace(/%/g, '');
                const parsedCapRate = parseFloat(capRateStr);
                if (!isNaN(parsedCapRate)) {
                  capRate = parsedCapRate;
                }
              }
            }
            
            // Extract year built
            if (yearBuilt === null && yearBuiltKeywords.some(keyword => keyStr.includes(keyword))) {
              if (typeof value === 'number') {
                yearBuilt = value;
              } else if (typeof value === 'string') {
                const parsedYear = parseInt(value);
                if (!isNaN(parsedYear) && parsedYear > 1800 && parsedYear < 2100) {
                  yearBuilt = parsedYear;
                }
              }
            }
          });
        });
      });
      
      // Create property info object
      const propertyInfo = {
        propertyName,
        address,
        city,
        state,
        zip,
        purchasePrice: price,
        capRate,
        yearBuilt,
      };
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(propertyInfo, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error extracting property information: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  } else if (request.params.name === "generateAnalysisSpreadsheet") {
    const propertyData = request.params.arguments?.propertyData as Record<string, any>;
    const templateName = request.params.arguments?.templateName as string;
    
    if (!propertyData || !templateName) {
      return {
        content: [{ type: "text", text: "Property data and template name are required" }],
        isError: true,
      };
    }
    
    try {
      // Create a new workbook
      const workbook = XLSX.utils.book_new();
      
      // Create a worksheet with property data
      const worksheet = XLSX.utils.json_to_sheet([propertyData]);
      
      // Add the worksheet to the workbook
      XLSX.utils.book_append_sheet(workbook, worksheet, "Analysis");
      
      // Add a summary sheet
      const summaryData = [
        { Metric: "Property Name", Value: propertyData.propertyName || "N/A" },
        { Metric: "Purchase Price", Value: propertyData.purchasePrice || "N/A" },
        { Metric: "Cap Rate", Value: propertyData.capRate ? `${propertyData.capRate}%` : "N/A" },
        { Metric: "NOI", Value: propertyData.noi || "N/A" },
        { Metric: "Total Units", Value: propertyData.totalUnits || "N/A" },
        { Metric: "Occupancy Rate", Value: propertyData.occupancyRate ? `${propertyData.occupancyRate}%` : "N/A" },
        { Metric: "Average Rent", Value: propertyData.averageRent || "N/A" },
        { Metric: "Year Built", Value: propertyData.yearBuilt || "N/A" },
      ];
      
      const summaryWorksheet = XLSX.utils.json_to_sheet(summaryData);
      XLSX.utils.book_append_sheet(workbook, summaryWorksheet, "Summary");
      
      // Convert workbook to base64
      const outputBuffer = XLSX.write(workbook, { type: "buffer", bookType: "xlsx" });
      const outputBase64 = Buffer.from(outputBuffer).toString("base64");
      
      return {
        content: [
          {
            type: "text",
            text: `Analysis spreadsheet generated successfully for template: ${templateName}. Base64 output:\n${outputBase64.substring(0, 100)}...`,
          },
          {
            type: "blob",
            mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            blob: outputBase64,
          },
        ],
        isError: false,
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error generating analysis spreadsheet: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }
  
  throw new Error("Tool not found");
});

// Export the spreadsheet processing server
export function initializeSpreadsheetProcessingServer() {
  return spreadsheetProcessingServer;
}
