function comment(post_id){
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    $.ajax(
        {
            type: "POST",
            url: window.location.href + post_id + "/commentpost",
            headers: {'X-CSRFToken': csrftoken, "Authorization": "Token %s"},
            success : function(){
                alert("Comment posted succesfully");
                location.reload();
            }
        }
    )
}

