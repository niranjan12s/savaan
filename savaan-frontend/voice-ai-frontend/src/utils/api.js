import axios from "axios";
// import { API_URL } from "../config";

const API=axios.create({
    baseURL: "http://localhost:8000",
})

API.interceptors.request.use((config)=>{
    const token=localStorage.getItem('authToken');
    if(token) {
        config.headers.Authorization=`Bearer ${token}`;
    }
    return config
});

export default API;