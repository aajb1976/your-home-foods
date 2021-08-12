/* Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
    /* See LICENSE file for full copyright and licensing details. */
$(document).ready(function() 
{
	
	$('.image_div').hover(
	function()
		{

		$(this).find('.img-rounded').css({'border':'solid 1px #ddd'});
		
		},
	function()
		{
		$(this).find('.img-rounded').css({'border':'none'});
		});

}); 