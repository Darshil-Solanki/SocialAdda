const id = JSON.parse(document.getElementById('json-username').textContent);
const message_username = JSON.parse(document.getElementById('json-message-username').textContent);
const receiver = JSON.parse(document.getElementById('json-username-receiver').textContent);

var now = new Date();
var hours = now.getHours();
var minutes = now.getMinutes();
var meridian = hours < 12 ? 'AM' : 'PM';

// Convert from 24-hour to 12-hour format
hours = hours % 12;
hours = hours ? hours : 12;

// Add leading zeros to minutes if needed
minutes = ('0' + minutes).slice(-2);

// Construct the formatted time string
var timeString = hours + ':' + minutes + ' ' + meridian;

const socket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/'
    + id
    + '/'
);

socket.onopen = function(e){
    console.log("CONNECTION ESTABLISHED");
}

socket.onclose = function(e){
    console.log("CONNECTION LOST");
}

socket.onerror = function(e){
    console.log("ERROR OCCURED");
}

socket.onmessage = function(e){
    const data = JSON.parse(e.data);
    if(data.username == message_username){
        document.querySelector('#chat-body').innerHTML += `<tr>
                                                                <td class="chat-message">
                                                                <p class="bg-send p-2 mt-2 mr-5 shadow-sm text-white float-right rounded">${data.message}</p>
                                                                </td>
                                                                <td class="chat-time">
                                                                    <p><small class="p-1 shadow-sm">${timeString}</small>
                                                                    </p>
                                                                </td>
                                                            </tr>`
    }else{
        document.querySelector('#chat-body').innerHTML += `<tr>
                                                                <td  class="chat-message">
                                                                <p class="bg-receive p-2 mt-2 mr-5 shadow-sm text-white float-left rounded">${data.message}</p>
                                                                </td>
                                                                <td class="chat-time">
                                                                    <p><small class="p-1 shadow-sm">${timestring}</small>
                                                                    </p>
                                                                </td>
                                                            </tr>`
    }
}

document.querySelector('#chat-message-submit').onclick = function(e){
    const message_input = document.querySelector('#message_input');
    const message = message_input.value;

    socket.send(JSON.stringify({
        'message':message,
        'username':message_username,
        'receiver':receiver
    }));

    message_input.value = '';
}