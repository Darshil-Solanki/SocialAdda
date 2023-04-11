
document.addEventListener('DOMContentLoaded', () => {
    let active = document.querySelector('.body').dataset.page;
    if (active !="" & active!="chat-messages") {
        document.querySelector("#"+active).classList.add('active');
    }
    
    var loadMore = document.getElementById("more-suggestions");
    var offset = Number(loadMore.getAttribute("data-offset"));
    var usernames = Array.from(
        document.querySelectorAll(".user-details .grey")
      ).map((el) => el.innerHTML.trim().substr(1));

    loadMore.addEventListener("click", function(event) {
        event.preventDefault();
        fetch("/n/more_suggestions",{
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'usernames': usernames,
                'offset': offset
            })
        })
            .then(response => response.json())
            .then(data => {
                let suggestions = data.suggestions;
                let allUsersRetrieved = data.all_sent;
                // append new suggestions to the list
                suggestions.forEach(suggestion => {
                    const suggestionsContainer=document.querySelector(".suggestion-box");
                    usernames.push(suggestion.username);
                    var userDiv = document.createElement("div");
                    userDiv.classList.add("suggestion-user");
                    userDiv.innerHTML=`
                    <div>
                        <a href="{% url 'profile' suggestion.username %}">
                            <div class="small-profilepic" style="background-image: url(${suggestion.profile_pic})"></div>
                        </a>
                    </div>
                    <div class="user-details">
                        <a href="{% url 'profile' suggestion.username %}">
                            <div id="user-name">
                                <strong>
                                    ${suggestion.first_name} ${suggestion.last_name}
                                </strong>
                            </div>
                            <div class="grey">@${suggestion.username}</div>
                        </a>
                    </div>
                    <div>
                        <button class="btn btn-outline-info " type="button" onclick="follow_user(this,'${suggestion.username}','suggestion')">Follow</button>
                    </div>`;
                    suggestionsContainer.insertBefore(userDiv,suggestionsContainer.lastElementChild)

                });
                offset += suggestions.length;
                loadMore.setAttribute("data-offset", offset);
                if(allUsersRetrieved){
                    document.getElementById("more-suggestions").style.display='none';
                }
            })
            .catch(error => {
                console.error(error);
            });
    });
});

function drop_down(event) {
    let drop_down = event.target.parentElement.querySelector(".dropdown-menu");
    setTimeout(() => {
        drop_down.style.display = 'block';
        width = drop_down.offsetWidth;
        let btn_width = drop_down.parentElement.querySelector('button').offsetWidth;
        let left = width-btn_width;
        drop_down.style.left = '-'+left+'px';
        document.addEventListener('keydown', event => {
            if(event.key === 'Escape') {
                drop_down.style.display = 'none';
            }
        });
    }, 100);
}

function remove_drop_down(event) {
    setTimeout(() => {
        event.target.parentElement.querySelector(".dropdown-menu").style.display = 'none';
    },250);
}

function createpost() {
    let popup = document.querySelector(".popup");
    popup.style.display = 'block';
    popup.querySelector('.large-popup').style.display = 'block'
    document.querySelector('.body').setAttribute('aria-hidden', 'true');
    document.querySelector('body').style.overflow = "hidden";
    document.querySelector('#insert-img').onchange = previewFile;
    popup.querySelector('.large-popup').querySelector('form').setAttribute('onsubmit', '');
    popup.querySelector('.large-popup').querySelector("#post-text").addEventListener('input', (event) => {
        if(event.target.value.trim().length > 0) {
            popup.querySelector('.submit-btn').disabled = false;
        }
        else if(event.target.parentElement.querySelector('#img-div').style.backgroundImage) {
            popup.querySelector('.submit-btn').disabled = false;
        }
        else {
            popup.querySelector('.submit-btn').disabled = true;
        }
    });
}

function confirm_delete(id) {
    let popup = document.querySelector('.popup');
    popup.style.display = 'block';
    let small_popup = popup.querySelector('.small-popup');
    small_popup.style.display = 'block';
    document.querySelector('.body').setAttribute('aria-hidden', 'true');
    document.querySelector('body').style.overflow = "hidden";
    small_popup.querySelector('#delete_post_btn').setAttribute('onclick', `delete_post(${id})`);
}

function delete_post(id) {
    remove_popup();
    setTimeout(() => {
        let post = 0;
        document.querySelectorAll('.post').forEach(eachpost => {
            if(eachpost.dataset.post_id==id) {
                post = eachpost;
            }
        });
        post.style.animationPlayState = 'running';
        post.addEventListener('animationend', () => {
            post.remove();
        });
        fetch('/n/post/'+parseInt(id)+'/delete', {
            method: 'PUT'
        });
    },200);
}
function edit_del_img(image){
    document.querySelector(`#${image}-image-input`).value = '';
    if(image=="cover"){
        document.querySelector(`.edit-${image}-image`).style.backgroundImage = 'url("/media/uploadCover.png")';
    }else{
        document.querySelector(`.edit-${image}-image`).style.backgroundImage = 'url("/media/uploadProfile.png")';
    }
    document.querySelector(".profile-popup").querySelector('.form-action-btns').querySelector('input[type=submit]').disabled = false;
    document.querySelector(`.${image}-del-img`).style.display="none";
    document.querySelector('.profile-popup').querySelector(`#${image}-img-change`).value = 'true';
}
function remove_profileform(){
    document.querySelector('.popup').style.display='none';
    document.querySelector('.body').setAttribute('aria-hidden', 'false');
    document.querySelector('body').style.overflow = "auto";
    document.querySelector("#eprofile_form").style.display='none';
    document.querySelector
    document.querySelector('#name-change').value = '';
    let name=document.querySelector("#name").textContent.split(" ");
    document.querySelector('#first-name').value = name[0];
    document.querySelector('#last-name').value = name[1];
    document.querySelector('#cover-img-change').value='';
    document.querySelector('#profile-img-change').value='';
    let coverImage=document.querySelector('.cover-image').style.backgroundImage;
    let profileImage=document.querySelector('.profile-view').querySelector('.profile-image').style.backgroundImage;
    document.querySelector('.edit-cover-image').style.backgroundImage=coverImage;
    document.querySelector('.edit-profile-image').style.backgroundImage=profileImage;
    document.querySelector('#cover-image-input').value='';
    document.querySelector('#profile-image-input').value='';
    document.querySelector(".profile-popup").querySelector('.form-action-btns').querySelector('input[type=submit]').disabled = true;

}
function edit_profile(){
    let popup=document.querySelector('.popup');
    popup.style.display='block';
    document.querySelector('.body').setAttribute('aria-hidden', 'true');
    document.querySelector('body').style.overflow = "hidden";
    document.querySelector("#eprofile_form").style.display='block';
    const inputs = document.querySelector(".edit-profile-popup").querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
    input.addEventListener('input', (event) => {
        document.querySelector('.profile-popup').querySelector('#name-change').value = 'true';
        document.querySelector(".profile-popup").querySelector('.form-action-btns').querySelector('input[type=submit]').disabled = false;
    });
    });
    document.querySelector('#cover-image-input').onchange = function(){
        previewProfileFiles('cover')
    };
    document.querySelector('#profile-image-input').onchange = function(){
        previewProfileFiles('profile')
    };
    profile_image=document.querySelector(".edit-profile-image").style.backgroundImage;
    cover_image=document.querySelector(".edit-cover-image").style.backgroundImage;
    if(cover_image) {
        document.querySelector('.cover-del-img').addEventListener('click',function(){ edit_del_img('cover')});
        document.querySelector('.cover-del-img').style.display='block';
        popup.querySelector('.edit-cover-image').style.display = 'block';
    }
    if(profile_image) {
        document.querySelector('.profile-del-img').addEventListener('click', function(){edit_del_img('profile')});
        document.querySelector('.profile-del-img').style.display='block';
    }
    
}
function previewProfileFiles(image) {
    document.querySelector(`.${image}-spinner`).style.display = 'block';
    document.querySelector(`.${image}-del-img`).style.display = 'none';
    var preview = document.querySelector(`.edit-${image}-image`);
    var file    = document.querySelector(`#${image}-image-input`).files[0];
    var reader  = new FileReader();
    
    reader.onloadend = function () {
        preview.style.backgroundImage = `url(${reader.result})`;
        document.querySelector(`#${image}-img-change`).value = 'true';
    }

    if (file) {
        document.querySelector(".profile-popup").querySelector('.form-action-btns').querySelector('input[type=submit]').disabled = false;
        var promise = new Promise(function(resolve, reject){
            setTimeout(() => {
                var read = reader.readAsDataURL(file);
                resolve(read);
            },500);
        });
        promise 
        .then(function(){
            document.querySelector(`.${image}-spinner`).style.display = 'none';
            document.querySelector(`.${image}-del-img`).style.display = 'block';
            if(image=="cover"){
                document.querySelector(`.${image}-del-img`).addEventListener('click', function(){ edit_del_img('cover')});
            }
            else{
                document.querySelector(`.${image}-del-img`).addEventListener('click', function(){ edit_del_img('profile')});
            }
        })
        .catch(function () { 
            console.log('Some error has occured'); 
            });    
    }
    else{
        document.querySelector(`.${image}-spinner`).style.display = 'none';
        document.querySelector(`.${image}-del-img`).style.display = 'block';
        if(image=="cover"){
            document.querySelector(`.${image}-del-img`).addEventListener('click', function(){ edit_del_img('cover')});
        }
        else{
            document.querySelector(`.${image}-del-img`).addEventListener('click', function(){ edit_del_img('profile')});
        }
    }

}


function edit_post(element) {
    let post = element.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement;
    let popup = document.querySelector('.large-popup');
    let promise = new Promise((resolve, reject) => {
        let post_text = post.querySelector('.post-content').innerText;
        let post_image = post.querySelector('.post-image').style.backgroundImage;

        popup.querySelector('#post-text').value = post_text;
        if(post_image) {
            popup.querySelector('#img-div').style.backgroundImage = post_image;
            document.querySelector('#del-img').addEventListener('click', del_image);
            popup.querySelector('#img-div').style.display = 'block';
        }
        else {
            popup.querySelector('#img-div').style.backgroundImage = '';
        }
        resolve(popup);
    });
    promise.then(() => {
        createpost();
        popup.querySelector('form').setAttribute('onsubmit', `return edit_post_submit(${post.dataset.post_id})`);
        popup.querySelector('.submit-btn').disabled = false;
    });
}
function edit_post_submit(post_id) {
    let popup = document.querySelector('.large-popup');
    let text = popup.querySelector('#post-text').value;
    let pic = popup.querySelector('#insert-img');
    let chg = popup.querySelector('#img-change');
    let formdata = new FormData();
    formdata.append('text',text);
    formdata.append('picture',pic.files[0]);
    formdata.append('img_change', chg.value);
    formdata.append('id',post_id);
    fetch('/n/post/'+parseInt(post_id)+'/edit', {
        method:'POST',
        body: formdata
    })
    .then(response => response.json())
    .then(response => {
        if(response.success) {
            let posts = document.querySelectorAll('.post');
            posts.forEach(post => {
                if(parseInt(post.dataset.post_id) === parseInt(post_id)) {
                    if(response.text) {
                        post.querySelector('.post-content').innerText = response.text;
                    }
                    else {
                        post.querySelector('.post-content').innerText = "";
                    }
                    if(response.picture) {
                        post.querySelector('.post-image').style.backgroundImage = `url(${response.picture})`;
                        post.querySelector('.post-image').style.display = 'block';
                    }
                    else {
                        post.querySelector('.post-image').style.backgroundImage = '';
                        post.querySelector('.post-image').style.display = 'none';
                    }
                }
            });
            return false;
        }
        else {
            console.log('There was an error while editing the post.');
        }
    });
    remove_popup();
    return false;
}

function remove_popup() {
    let popup = document.querySelector('.popup');
    popup.style.display = 'none';
    document.querySelector('.body').style.marginRight = '0px';
    document.querySelector('.body').setAttribute('aria-hidden', 'false');
    document.querySelector('body').style.overflow = "auto";
    let small_popup = document.querySelector('.small-popup');
    let large_popup = document.querySelector('.large-popup');
    small_popup.style.display = 'none';
    large_popup.style.display = 'none';
    large_popup.querySelector('#post-text').value = '';
    large_popup.querySelector('#insert-img').value = '';
    large_popup.querySelector('#img-div').style.backgroundImage = '';
    large_popup.querySelector('#img-change').value = 'false';
    large_popup.querySelector('#img-div').style.display = 'none';
}

function previewFile() {
    document.querySelector('#img-div').style.display = 'block';
    document.querySelector('#spinner').style.display = 'block';
    document.querySelector('#del-img').style.display = 'none';
    document.querySelector('#del-img').addEventListener('click', del_image);
    var preview = document.querySelector('#img-div');
    var file    = document.querySelector('input[type=file]').files[0];
    var reader  = new FileReader();
    
    reader.onloadend = function () {
        preview.style.backgroundImage = `url(${reader.result})`;
        document.querySelector('.large-popup').querySelector('#img-change').value = 'true';
    }

    if (file) {
        document.querySelector('.form-action-btns').querySelector('input[type=submit]').disabled = false;
        var promise = new Promise(function(resolve, reject){
            setTimeout(() => {
                var read = reader.readAsDataURL(file);
                resolve(read);
            },500);
        });
        promise
            .then(function () { 
                document.querySelector('#spinner').style.display = 'none';
                document.querySelector('#del-img').style.display = 'block';
            }) 
            .catch(function () { 
                console.log('Some error has occured'); 
            });    
    }
    else{
        document.querySelector('#spinner').style.display = 'none';
        document.querySelector('#del-img').style.display = 'block';
    }
}

function del_image() {
    document.querySelector('input[type=file]').value = '';
    document.querySelector('#img-div').style.backgroundImage = '';
    document.querySelector('#img-div').style.display = 'none';
    document.querySelector('.large-popup').querySelector('#img-change').value = 'true';
    if(document.querySelector('.large-popup').querySelector('#post-text').value.trim().length <= 0) {
        document.querySelector('.large-popup').querySelector('.form-action-btns').querySelector('input[type=submit]').disabled = true;
    }
}

function like_post(element) {
    if(document.querySelector('#user_is_authenticated').value === 'False') {
        return false;
    }
    let id = element.dataset.post_id;
    fetch('/n/post/'+parseInt(id)+'/like', {
        method: 'PUT'
    })
    .then(() => {
        let count = element.querySelector('.likes_count');
        let value = count.innerHTML;
        value++;
        count.innerHTML = value;
        element.querySelector('.svg-span').innerHTML = `
            <svg width="1.1em" height="1.1em" viewBox="0 -1 16 16" class="bi bi-heart-fill" fill="#e0245e" xmlns="http://www.w3.org/2000/svg">
                <path fill-rule="evenodd" d="M8 1.314C12.438-3.248 23.534 4.735 8 15-7.534 4.736 3.562-3.248 8 1.314z"/>
            </svg>`;
        element.setAttribute('onclick','unlike_post(this)');
    })
}

function unlike_post(element) {
    let id = element.dataset.post_id;
    fetch('/n/post/'+parseInt(id)+'/unlike', {
        method: 'PUT'
    })
    .then(() => {
        let count = element.querySelector('.likes_count');
        let value = count.innerHTML;
        value--;
        count.innerHTML = value;
        element.querySelector('.svg-span').innerHTML = `
            <svg width="1.1em" height="1.1em" viewBox="0 -1 16 16" class="bi bi-heart" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path fill-rule="evenodd" d="M8 2.748l-.717-.737C5.6.281 2.514.878 1.4 3.053c-.523 1.023-.641 2.5.314 4.385.92 1.815 2.834 3.989 6.286 6.357 3.452-2.368 5.365-4.542 6.286-6.357.955-1.886.838-3.362.314-4.385C13.486.878 10.4.28 8.717 2.01L8 2.748zM8 15C-7.333 4.868 3.279-3.04 7.824 1.143c.06.055.119.112.176.171a3.12 3.12 0 0 1 .176-.17C12.72-3.042 23.333 4.867 8 15z"/>
            </svg>`;
        element.setAttribute('onclick','like_post(this)');
    })
}

function save_post(element) {
    let id = element.dataset.post_id;
    fetch('/n/post/'+parseInt(id)+'/save', {
        method: 'PUT'
    })
    .then(() => {
        element.querySelector('.svg-span').innerHTML = `
            <svg width="1.1em" height="1.1em" viewBox="0.5 0 15 15" class="bi bi-bookmark-fill" fill="#17bf63" xmlns="http://www.w3.org/2000/svg">
                <path fill-rule="evenodd" d="M3 3a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v12l-5-3-5 3V3z"/>
            </svg>`;
        element.setAttribute('onclick','unsave_post(this)');
    });
}

function unsave_post(element) {
    let id = element.dataset.post_id;
    fetch('/n/post/'+parseInt(id)+'/unsave', {
        method: 'PUT'
    })
    .then(() => {
        element.querySelector('.svg-span').innerHTML = `
        <svg width="1.1em" height="1.1em" viewBox="0.5 0 15 15" class="bi bi-bookmark" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" d="M8 12l5 3V3a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v12l5-3zm-4 1.234l4-2.4 4 2.4V3a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10.234z"/>
        </svg>`;
        element.setAttribute('onclick','save_post(this)');
    });
}


function follow_user(element, username,origin) {
    fetch('/'+username+'/follow', {
        method: 'PUT'
    })
    .then(() => {
        if(origin === 'suggestion') {
            element.parentElement.innerHTML = `<button class="btn btn-blue" type="button" onclick="unfollow_user(this,'${username}','suggestion')">Following</button>`;
        }
        else if(origin === 'profile_page') {
            element.parentElement.innerHTML = `<button class="btn btn-blue float-right" onclick="unfollow_user(this,'${username}','profile_page')" id="following-btn">Following</button>`;
        }
        if(document.querySelector('.body').dataset.page === 'profile') {
            if(document.querySelector('.profile-view').dataset.user === username) {
                document.querySelector('#follower__count').innerHTML++;
            }
        }
    });
}

function unfollow_user(element, username,origin) {
    fetch('/'+username+'/unfollow', {
        method: 'PUT'
    })
    .then(() => {
        if(origin === 'suggestion') {
            element.parentElement.innerHTML = `<button class="btn btn-outline-info" type="button" onclick="follow_user(this,'${username}','suggestion')">Follow</button>`;
        }
        else if(origin === 'profile_page') {
            element.parentElement.innerHTML = `<button class="btn btn-outline-info float-right" onclick="follow_user(this,'${username}','profile_page')">Follow</button>`;
        }
        if(document.querySelector('.body').dataset.page === 'profile') {
            if(document.querySelector('.profile-view').dataset.user === username) {
                document.querySelector('#follower__count').innerHTML--;
            }
        }
    });
}


function show_comment(element) {
    let post_div = element.parentElement.parentElement.parentElement.parentElement;
    let post_id = post_div.dataset.post_id;
    let comment_div = post_div.querySelector('.comment-div');
    let comment_div_data = comment_div.querySelector('.comment-div-data');
    let comment_comments = comment_div_data.querySelector('.comment-comments');
    if(comment_div.style.display === 'block') {
        comment_div.querySelector('input').focus()
        return;
    }
    comment_div.querySelector('#spinner').style.display = 'block';
    comment_div.style.display = 'block';
    fetch('/n/post/'+parseInt(post_id)+'/comments')
    .then(response => response.json())
    .then(comments => {
        comments.forEach(comment => {
            display_comment(comment,comment_comments);
        });
    })
    .then(() => {
        setTimeout(() => {
            comment_div.querySelector('.spinner-div').style.display = 'none';
            comment_div.querySelector('.comment-div-data').style.display = 'block';
            comment_div.style.overflow = 'auto';
        }, 500);
    });
}

function write_comment(element) {
    let post_id = element.parentElement.parentElement.parentElement.parentElement.parentElement.dataset.post_id;
    let comment_text = element.querySelector('.comment-input').value;
    let comment_comments = element.parentElement.parentElement.parentElement.parentElement.querySelector('.comment-comments');
    let comment_count = comment_comments.parentElement.parentElement.parentElement.querySelector('.cmt-count');
    if(comment_text.trim().length <= 0) {
        return false;
    }
    fetch('/n/post/'+parseInt(post_id)+'/write_comment',{
        method: 'POST',
        body: JSON.stringify({
            comment_text: comment_text
        })
    })
    .then(response => response.json())
    .then(comment => {
        console.log(comment);
        element.querySelector('input').value = '';
        comment_count.innerHTML++;
        display_comment(comment[0],comment_comments,true);
        return false;
    });
    return false;
}

function display_comment(comment, container, new_comment=false) {
    let writer = document.querySelector('#user_is_authenticated').dataset.username;
    let eachrow = document.createElement('div');
    eachrow.className = 'eachrow';
    eachrow.setAttribute('data-id', comment.id);
    eachrow.innerHTML = `
        <div>
            <a href='/${comment.commenter.username}'>
                <div class="small-profilepic" style="background-image: url(${comment.commenter.profile_pic})"></div>
            </a>
        </div>
        <div style="flex: 1;">
            <div class="comment-text-div">
                <div class="comment-user">
                    <a href="/${comment.commenter.username}">
                        ${comment.commenter.first_name} ${comment.commenter.last_name}
                    </a>
                </div>
                ${comment.body}
            </div>
        </div>`;
    if (new_comment) {
        eachrow.classList.add('godown');
        let comments = container.innerHTML;
        container.prepend(eachrow);
    }
    else {
        container.append(eachrow);
    }
}