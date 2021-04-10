function likePost(post_id) {
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    $.ajax(
        {
            type: "POST",
            url: window.location.href + post_id + "/likepost/",
            headers: { 'X-CSRFToken': csrftoken, "Authorization": "Token %s" },
            success: function () {
                alert("Successfully liked post!");
                location.reload();
            },
            error: function (response) {
                if(response.status == 409) {alert("You've already liked this post.");}
                else {console.log(response);}
            }
        }
    )
}

function likeComment(comment_id) {
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    $.ajax(
        {
            type: "POST",
            url: window.location.href + comment_id + "/likecomment/",
            headers: { 'X-CSRFToken': csrftoken, "Authorization": "Token %s" },
            success: function () {
                alert("Successfully liked comment!");
                location.reload();
            },
            error: function (response) {
                if(response.status == 409) {alert("You've already liked this comment.");}
                else {console.log(response);}
            }
        }
    )
}

function viewLikes(post_id) {
    location.replace(window.location.href + post_id + "/likes/")
}

function commentPost(post_id){
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    location.replace(window.location.href + post_id + "/commentpost/")

}

function viewComment(post_id){
    location.replace(window.location.href + post_id + "/viewComments/")
}

