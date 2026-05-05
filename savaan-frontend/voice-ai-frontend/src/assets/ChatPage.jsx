import { useState, useEffect, useRef } from "react";
import API from "../utils/api";

export default function ChatInterface() {
    const [isRecording, setIsRecording] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [showStats, setShowStats] = useState(true);
    const [messages, setMessages] = useState([]);
    const [userDopamine, setUserDopamine] = useState(0);
    const [userSurvival, setUserSurvival] = useState(0);
    const [aiDopamine, setAiDopamine] = useState(0);
    const [aiSurvival, setAiSurvival] = useState(0);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const handleRecord = async (e) => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mediaRecorder = new MediaRecorder(stream);
                mediaRecorderRef.current = mediaRecorder;
                chunksRef.current = [];
                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) {
                        chunksRef.current.push(e.data);
                    }
                };
                mediaRecorder.onstop = async (e) => {
                    const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                    await handleAudioSubmit(blob);
                };
                mediaRecorder.start();
                setIsRecording(true);
            } catch (err) {
                mediaRecorderRef.current.stop();
                setIsRecording(false);
            }
        } else {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    }

    const handleAudioSubmit = async (audioBlob) => {
        setIsThinking(true);
        const formData = new FormData();
        formData.set("file", audioBlob);
        try {
            const userId=localStorage.getItem('userId');
            const response = await API.post(`/users/${userId}/respond`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            const data = response.data;
            setAiDopamine(data.metrics.dopamine_ai);
            setAiSurvival(data.metrics.survival_ai);
            setUserDopamine(data.metrics.dopamine_user);
            setUserSurvival(data.metrics.survival_user);
            setMessages(prev => [...prev, { from: "user", text: data.transcript }, { from: "ai", text: data.response }])
        } catch (error) {
            console.error("API call failed:", error);
        } finally {
            setIsThinking(false);
        }
    }

    return (
        <div className="flex h-screen">
            <div className="flex flex-col flex-1 bg-gray-100">
                <div className="flex-1 overflow-y-auto p-4 flex flex-col space-y-2">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`p-2 rounded ${msg.from === "ai" ? "bg-gray-200 text-black self-start" : "bg-blue-500 text-white self-end"
                                } max-w-xs`}
                        >
                            {msg.text}
                        </div>
                    ))}
                </div>


                <div className="p-4 flex items-center justify-between bg-gray shadow">
                    <button
                        onClick={handleRecord}
                        className="bg-gray-100 text-white px-4 py-2 rounded hover:bg-blue-700"
                    >
                        🎙️ {isRecording ? 'Stop' : 'Start'} Talking to Savaan
                    </button>

                    {isThinking && (
                        <span className="text-gray-600 italic ml-4">
                            Savaan is thinking...
                        </span>
                    )}
                </div>
            </div>
            {showStats && (
                <div className="w-72 bg-white p-4 shadow-lg">
                    <h3 className="text-lg font-semibold mb-4">AI & User Status</h3>

                    <div className="mb-4">
                        <label className="text-sm text-gray-700">AI Dopamine</label>
                        <div className="w-full bg-gray-200 rounded h-4 mt-1">
                            <div
                                className="bg-green-500 h-4 rounded"
                                style={{ width: `${aiDopamine * 100}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="mb-4">
                        <label className="text-sm text-gray-700">AI Survival</label>
                        <div className="w-full bg-gray-200 rounded h-4 mt-1">
                            <div
                                className="bg-red-500 h-4 rounded"
                                style={{ width: `${aiSurvival * 100}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="mb-4">
                        <label className="text-sm text-gray-700">User Dopamine</label>
                        <div className="w-full bg-gray-200 rounded h-4 mt-1">
                            <div
                                className="bg-yellow-500 h-4 rounded"
                                style={{ width: `${userDopamine * 100}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="mb-4">
                        <label className="text-sm text-gray-700">User Survival</label>
                        <div className="w-full bg-gray-200 rounded h-4 mt-1">
                            <div
                                className="bg-blue-500 h-4 rounded"
                                style={{ width: `${userSurvival * 100}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            )};
        </div>

    );
}