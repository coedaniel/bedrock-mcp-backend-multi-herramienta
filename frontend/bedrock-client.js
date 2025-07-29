/**
 * 🚀 Bedrock Client - Amazon Q CLI Style
 * Cliente para integración con Amazon Bedrock Converse API + Function Calling
 */

class BedrockClient {
    constructor() {
        this.modelId = 'anthropic.claude-3-5-sonnet-20241022-v2:0';
        this.region = 'us-east-1';
        this.backendUrl = window.location.origin;
        this.conversationHistory = [];
        this.toolDefinitions = null;
        
        this.initializeAWS();
        this.loadToolDefinitions();
    }

    async initializeAWS() {
        // Configurar AWS SDK (en producción usar Cognito o IAM roles)
        AWS.config.update({
            region: this.region,
            credentials: new AWS.CognitoIdentityCredentials({
                IdentityPoolId: 'us-east-1:your-identity-pool-id' // Configurar en producción
            })
        });

        this.bedrock = new AWS.BedrockRuntime({
            region: this.region
        });
    }

    async loadToolDefinitions() {
        try {
            const response = await fetch(`${this.backendUrl}/bedrock/function-definitions`);
            const data = await response.json();
            this.toolDefinitions = data.functions;
            console.log('✅ Tool definitions loaded:', this.toolDefinitions);
        } catch (error) {
            console.error('❌ Error loading tool definitions:', error);
        }
    }

    async sendMessage(message) {
        // Agregar mensaje del usuario al historial
        this.conversationHistory.push({
            role: 'user',
            content: [{ text: message }]
        });

        try {
            // Preparar el request para Bedrock Converse API
            const request = {
                modelId: this.modelId,
                messages: this.conversationHistory,
                inferenceConfig: {
                    maxTokens: 4000,
                    temperature: 0.7,
                    topP: 0.9
                }
            };

            // Agregar tool definitions si están disponibles
            if (this.toolDefinitions && this.toolDefinitions.length > 0) {
                request.toolConfig = {
                    tools: this.toolDefinitions.map(tool => ({
                        toolSpec: {
                            name: tool.name,
                            description: tool.description,
                            inputSchema: {
                                json: tool.parameters
                            }
                        }
                    }))
                };
            }

            console.log('📤 Sending to Bedrock:', request);

            // Llamar a Bedrock Converse API
            const response = await this.bedrock.converse(request).promise();
            console.log('📥 Bedrock response:', response);

            // Procesar la respuesta
            return await this.processBedrockResponse(response);

        } catch (error) {
            console.error('❌ Error calling Bedrock:', error);
            throw new Error(`Error de Bedrock: ${error.message}`);
        }
    }

    async processBedrockResponse(response) {
        const message = response.output.message;
        let finalResponse = '';

        // Agregar mensaje del asistente al historial
        this.conversationHistory.push(message);

        // Procesar contenido del mensaje
        for (const content of message.content) {
            if (content.text) {
                finalResponse += content.text + '\n';
            }
            
            if (content.toolUse) {
                // Ejecutar tool use
                const toolResult = await this.executeToolUse(content.toolUse);
                
                // Agregar tool result al historial
                this.conversationHistory.push({
                    role: 'user',
                    content: [{
                        toolResult: {
                            toolUseId: content.toolUse.toolUseId,
                            content: toolResult.content
                        }
                    }]
                });

                // Llamar a Bedrock nuevamente para que procese el tool result
                const followUpResponse = await this.continueConversation();
                finalResponse += followUpResponse;
            }
        }

        return finalResponse.trim();
    }

    async executeToolUse(toolUse) {
        console.log('🔧 Executing tool:', toolUse);

        try {
            // Llamar a nuestro backend (Amazon Q CLI style)
            const response = await fetch(`${this.backendUrl}/bedrock/tool-use`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    toolUse: toolUse,
                    conversationId: this.generateConversationId(),
                    messageId: this.generateMessageId()
                })
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ Tool result:', result);

            return result.toolResult;

        } catch (error) {
            console.error('❌ Error executing tool:', error);
            return {
                content: [{
                    text: `Error ejecutando herramienta ${toolUse.name}: ${error.message}`
                }]
            };
        }
    }

    async continueConversation() {
        try {
            const request = {
                modelId: this.modelId,
                messages: this.conversationHistory,
                inferenceConfig: {
                    maxTokens: 4000,
                    temperature: 0.7,
                    topP: 0.9
                }
            };

            if (this.toolDefinitions && this.toolDefinitions.length > 0) {
                request.toolConfig = {
                    tools: this.toolDefinitions.map(tool => ({
                        toolSpec: {
                            name: tool.name,
                            description: tool.description,
                            inputSchema: {
                                json: tool.parameters
                            }
                        }
                    }))
                };
            }

            const response = await this.bedrock.converse(request).promise();
            const message = response.output.message;

            // Agregar respuesta al historial
            this.conversationHistory.push(message);

            // Extraer texto de la respuesta
            let text = '';
            for (const content of message.content) {
                if (content.text) {
                    text += content.text + '\n';
                }
            }

            return text.trim();

        } catch (error) {
            console.error('❌ Error in follow-up:', error);
            return `Error procesando respuesta: ${error.message}`;
        }
    }

    generateConversationId() {
        return 'conv-' + Math.random().toString(36).substr(2, 9);
    }

    generateMessageId() {
        return 'msg-' + Math.random().toString(36).substr(2, 9);
    }

    clearHistory() {
        this.conversationHistory = [];
    }
}

// Instancia global del cliente
let bedrockClient;

// Función para llamar a Bedrock (usada por el HTML)
async function callBedrock(message) {
    if (!bedrockClient) {
        bedrockClient = new BedrockClient();
        // Esperar a que se carguen las tool definitions
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    return await bedrockClient.sendMessage(message);
}

// Función para limpiar historial
function clearConversation() {
    if (bedrockClient) {
        bedrockClient.clearHistory();
    }
    
    // Limpiar chat UI
    const chatMessages = document.getElementById('chatMessages');
    const systemMessage = chatMessages.querySelector('.system-message');
    chatMessages.innerHTML = '';
    if (systemMessage) {
        chatMessages.appendChild(systemMessage);
    }
}
