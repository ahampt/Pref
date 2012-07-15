	/************************************************************************************************************
	Copyright (C) December 2005  DTHMLGoodies.com, Alf Magne Kalleland

	This library is free software; you can redistribute it and/or
	modify it under the terms of the GNU Lesser General Public
	License as published by the Free Software Foundation; either
	version 2.1 of the License, or (at your option) any later version.

	This library is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
	Lesser General Public License for more details.

	You should have received a copy of the GNU Lesser General Public
	License along with this library; if not, write to the Free Software
	Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

	Dhtmlgoodies.com., hereby disclaims all copyright interest in this script
	written by Alf Magne Kalleland.

	Alf Magne Kalleland, 2010
	Owner of DHTMLgoodies.com

	************************************************************************************************************/

	var arrow_offsetX=-5;var arrow_offsetY=0;var arrow_offsetX_firefox=-6;var arrow_offsetY_firefox=-13;var verticalSpaceBetweenListItems=3;var indicateDestionationByUseOfArrow=true;var lockedAfterDrag=false;var dragDropTopContainer=false;var dragTimer=-1;var dragContentObj=false;var contentToBeDragged=false;var contentToBeDragged_src=false;var contentToBeDragged_next=false;var destinationObj=false;var dragDropIndicator=false;var ulPositionArray=new Array();var mouseoverObj=false;var MSIE=navigator.userAgent.indexOf('MSIE')>=0?true:false;var navigatorVersion=navigator.appVersion.replace(/.*?MSIE (\d\.\d).*/g,'$1')/1;var destinationBoxes=new Array();var indicateDestinationBox=false;function getTopPos(inputObj){var returnValue=inputObj.offsetTop;while((inputObj=inputObj.offsetParent)!=null){if(inputObj.tagName!='HTML')returnValue+=inputObj.offsetTop}return returnValue}function getLeftPos(inputObj){var returnValue=inputObj.offsetLeft;while((inputObj=inputObj.offsetParent)!=null){if(inputObj.tagName!='HTML')returnValue+=inputObj.offsetLeft}return returnValue}function cancelEvent(){return false}function initDrag(e){if(document.all)e=event;if(lockedAfterDrag&&this.parentNode.id!='allItems')return;var st=Math.max(document.body.scrollTop,document.documentElement.scrollTop);var sl=Math.max(document.body.scrollLeft,document.documentElement.scrollLeft);dragTimer=0;dragContentObj.style.left=e.clientX+sl+'px';dragContentObj.style.top=e.clientY+st+'px';contentToBeDragged=this;contentToBeDragged_src=this.parentNode;contentToBeDragged_next=false;if(this.nextSibling){contentToBeDragged_next=this.nextSibling;if(!this.tagName&&contentToBeDragged_next.nextSibling)contentToBeDragged_next=contentToBeDragged_next.nextSibling}timerDrag();return false}function timerDrag(){if(dragTimer>=0&&dragTimer<10){dragTimer++;setTimeout('timerDrag()',10);return}if(dragTimer==10){dragContentObj.style.display='block';dragContentObj.appendChild(contentToBeDragged)}}function moveDragContent(e){if(dragTimer<10){if(contentToBeDragged){if(contentToBeDragged_next){contentToBeDragged_src.insertBefore(contentToBeDragged,contentToBeDragged_next)}else{contentToBeDragged_src.appendChild(contentToBeDragged)}}return}if(document.all)e=event;var st=Math.max(document.body.scrollTop,document.documentElement.scrollTop);var sl=Math.max(document.body.scrollLeft,document.documentElement.scrollLeft);dragContentObj.style.left=e.clientX+sl+'px';dragContentObj.style.top=e.clientY+st+'px';if(mouseoverObj)mouseoverObj.className='';destinationObj=false;dragDropIndicator.style.display='none';var x=e.clientX+sl;var y=e.clientY+st;var width=dragContentObj.offsetWidth;var height=dragContentObj.offsetHeight;var tmpOffsetX=arrow_offsetX;var tmpOffsetY=arrow_offsetY;if(!document.all){tmpOffsetX=arrow_offsetX_firefox;tmpOffsetY=arrow_offsetY_firefox}for(var no=0;no<ulPositionArray.length;no++){var ul_leftPos=ulPositionArray[no]['left'];var ul_topPos=ulPositionArray[no]['top'];var ul_height=ulPositionArray[no]['height'];var ul_width=ulPositionArray[no]['width'];if((x+width)>ul_leftPos&&x<(ul_leftPos+ul_width)&&(y+height)>ul_topPos&&y<(ul_topPos+ul_height)){dragDropIndicator.style.left=ul_leftPos+tmpOffsetX+'px';var subLi=ulPositionArray[no]['obj'].getElementsByTagName('LI');for(var liIndex=0;liIndex<subLi.length;liIndex++){var tmpTop=getTopPos(subLi[liIndex]);if(!indicateDestionationByUseOfArrow){if(y<tmpTop){destinationObj=subLi[liIndex];subLi[liIndex].parentNode.insertBefore(indicateDestinationBox,subLi[liIndex]);break}}else{if(y<tmpTop){destinationObj=subLi[liIndex];dragDropIndicator.style.top=tmpTop+tmpOffsetY-Math.round(dragDropIndicator.clientHeight/2)+'px';dragDropIndicator.style.display='block';break}}}if(!destinationObj)destinationObj=ulPositionArray[no]['obj'];mouseoverObj=ulPositionArray[no]['obj'].parentNode;mouseoverObj.className='mouseover';return}}}function dragDropEnd(e){if(dragTimer==-1)return;if(dragTimer<10){dragTimer=-1;return}dragTimer=-1;if(document.all)e=event;if(destinationObj){if(destinationObj.id=='allItems'||destinationObj.parentNode.id=='allItems')contentToBeDragged.className='';if(destinationObj.tagName=='UL'){destinationObj.appendChild(contentToBeDragged)}else{destinationObj.parentNode.insertBefore(contentToBeDragged,destinationObj)}mouseoverObj.className='';destinationObj=false;dragDropIndicator.style.display='none';contentToBeDragged=false;reNumberNodes();return}if(contentToBeDragged_next){contentToBeDragged_src.insertBefore(contentToBeDragged,contentToBeDragged_next)}else{contentToBeDragged_src.appendChild(contentToBeDragged)}contentToBeDragged=false;dragDropIndicator.style.display='none';mouseoverObj=false;reNumberNodes()}function initDragDropScript(){dragContentObj=document.getElementById('dragContent');dragDropIndicator=document.getElementById('dragDropIndicator');dragDropTopContainer=document.getElementById('dhtmlgoodies_dragDropContainer');document.documentElement.onselectstart=cancelEvent;var listItems=dragDropTopContainer.getElementsByTagName('LI');var itemHeight=false;for(var no=0;no<listItems.length;no++){listItems[no].onmousedown=initDrag;listItems[no].onselectstart=cancelEvent;if(!itemHeight)itemHeight=listItems[no].offsetHeight;if(MSIE&&navigatorVersion/1<6){listItems[no].style.cursor='hand'}}document.documentElement.onmousemove=moveDragContent;document.documentElement.onmouseup=dragDropEnd;var ulArray=dragDropTopContainer.getElementsByTagName('UL');for(var no=0;no<ulArray.length;no++){ulPositionArray[no]=new Array();ulPositionArray[no]['left']=getLeftPos(ulArray[no]);ulPositionArray[no]['top']=getTopPos(ulArray[no]);ulPositionArray[no]['width']=ulArray[no].offsetWidth;ulPositionArray[no]['height']=ulArray[no].clientHeight;ulPositionArray[no]['obj']=ulArray[no]}if(!indicateDestionationByUseOfArrow){indicateDestinationBox=document.createElement('LI');indicateDestinationBox.id='indicateDestination';indicateDestinationBox.style.display='none';document.body.appendChild(indicateDestinationBox)}}function saveArrangableNodes(){var arrParent=document.getElementById('allItems');var nodes=arrParent.getElementsByTagName('LI');var string="";for(var no=0;no<nodes.length;no++){if(string.length>0)string=string+',';string=string+nodes[no].id}document.forms["rankForm"].elements["hiddenMovieIds"].value=string;document.forms["rankForm"].submit()}
	function reNumberNodes()
	{
		var foundUnranked = false;
		var arrParent = document.getElementById('allItems');
		var nodes = arrParent.getElementsByTagName('LI');
		for(var no=0;no<nodes.length;no++){
			var oldHTML = nodes[no].innerHTML
			if (oldHTML.length > 9 && oldHTML.substring(0, 9) == 'Unranked:'){
				if (!foundUnranked){
					foundUnranked = true;
					oldId = nodes[no].id;
					nodes[no].innerHTML = no+1 + "." + oldHTML.substring(oldHTML.indexOf(" "));
					nodes[no].id = oldId.substring(1);
				}
			}
			else{
				nodes[no].innerHTML = no+1 + oldHTML.substring(oldHTML.indexOf("."));
			}
		}
	}
	
	window.onload = initDragDropScript;
	/*END DHTML SCRIPT
	***********************************************************************************************************/
