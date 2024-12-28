// openai_api.js

document.getElementById("btn").addEventListener("click", function(event){
event.preventDefault();
const jsonData = {
    text: document.getElementById("inputai").value
};

    sendRequest({   
        url: "/openai_api/generate_impression",
        data: jsonData,
        csrfToken: csrfToken
        }
        
    ).then(data => {
        if (data.status === "success"){
            document.getElementById("answer").textContent = data.data;
        } else {
            document.getElementById("answer").textContent = data.message;
        }
        
    })
    .catch(error => {
        console.log(error)
        document.getElementById("answer").textContent = "An error occurred. Please try again.";
    });
});