@extends('layouts.app')

@section('content')
<div class="max-w-4xl mx-auto py-8 px-4">
    <div class="bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">
        <!-- Header -->
        <div class="bg-gradient-to-r from-green-600 to-emerald-600 px-8 py-6 text-white">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
                    <span class="text-3xl">🤖</span>
                </div>
                <div>
                    <h1 class="text-2xl font-bold">Ubernie Intelligence Agent</h1>
                    <p class="text-green-100 text-sm">We don’t just list your business — we upgrade it into a system.</p>
                </div>
            </div>
        </div>

        <!-- Chat Container -->
        <div class="p-8" x-data="agentChat()">
            <div class="space-y-6 mb-8 min-h-[420px]" id="chat-messages">
                <!-- Messages populated by Alpine -->
            </div>

            <!-- Input -->
            <div class="flex gap-3 border-t pt-6">
                <input type="text" 
                       x-model="message"
                       @keyup.enter="sendMessage"
                       class="flex-1 border border-gray-300 focus:border-green-500 rounded-2xl px-6 py-4 text-lg"
                       placeholder="Tell me about your business...">
                <button @click="sendMessage"
                        class="bg-green-600 hover:bg-green-700 text-white px-8 rounded-2xl font-semibold transition">
                    Send
                </button>
            </div>
        </div>
    </div>
</div>

<script>
function agentChat() {
    return {
        message: '',
        messages: [],
        
        init() {
            this.addMessage('agent', 'Hello! I\'m the Ubernie Business Intelligence Agent. Let\'s upgrade your business into a complete system. What is the name and type of your business?');
        },
        
        addMessage(type, text) {
            this.messages.push({ type, text });
            this.$nextTick(() => {
                const container = document.getElementById('chat-messages');
                container.scrollTop = container.scrollHeight;
            });
        },
        
        async sendMessage() {
            if (!this.message.trim()) return;
            
            this.addMessage('user', this.message);
            const userMsg = this.message;
            this.message = '';
            
            // Simulate agent processing (in real app this would call backend)
            setTimeout(() => {
                if (userMsg.toLowerCase().includes('restaurant') || userMsg.toLowerCase().includes('cafe')) {
                    this.addMessage('agent', 'Great! I\'ve diagnosed your business as Level 1 (Basic Presence). Missing: website, payments, structured profile.');
                    this.addMessage('agent', 'Would you like me to auto-build your full business system now?');
                } else {
                    this.addMessage('agent', 'Thank you. I\'m running a full diagnosis and generating your custom Business-in-a-Box bundle + ecosystem recommendations (C6 + RemotePay).');
                }
            }, 1200);
        }
    }
}
</script>
@endsection