<?php
include_once '/var/www/ziggy.brodiehome/includes/functions.php';

ziggy_session_start();

// Session Variables
if (isset($_SESSION["loggedin"])) {
	$user = $_SESSION["username"];
	$loggedin = true;
	}
else {
	$loggedin = false;
	}

// Other variables

$title = "ZiggyThermostat";
$favicon = "assets/images/favicon.gif";
?>    

<html>
	<head>
		<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
		<title><?php echo $title; ?></title>
		<link rel="stylesheet", href="../assets/css/fa-all.css"/>
		<link rel="stylesheet" href="../assets/css/master.css"/>
		<link rel="stylesheet" href="../assets/css/fa-all.css"/>
		<link rel="stylesheet" href="../assets/css/thermostat.css"/>
		<link rel="shortcut icon" href="../assets/images/favicon.gif" type="image/gif">
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
		<script src="../assets/js/master.js"></script>
		<script src="../assets/js/paho-mqtt.js"></script>
		<script src="../assets/js/thermostat.js"></script>
	</head>
	<body>
		<div id="left-wrapper" class="col-3 ctr">
			<div id="forecast-wrapper">
				<div id="title-lable" class="xlg-txt">Today's Forcast</div>
				<div id="HL-lable" class="lg-txt">High / Low</div>
				<div id="temp" class="lg-txt">
					<span id="tempHigh"></span>
					<span id="tempDivider"> / </span>
					<span id="tempLow"></span>
				</div>
				<img id="dailyIcon" src="../assets/images/weather/icon-set/GIF/50x50/na.gif" alt="d-icon" class="lg-img"></img>
				<div id="dailySummary" class="md-txt lower"></div>
			</div>
			<div id="current-wrapper">
				<div id="current-lable" class="xlg-txt">Current Weather</div>
				<div id="currentTemp" class="xxlg-txt">Current Temp</div>
				<img id="currentIcon" src="../assets/images/weather/icon-set/GIF/50x50/na.gif" alt="c-icon" class="lg-img"></img>
				<div id="currentSummary" class="md-txt"></div>
			</div>
		</div>
		<div id="inside-wrapper" class="col-5 ctr">
			<div id="long-date" class="lg-txt ctr">Date</div>
			<div id="short-clock" class="jumbo-txt">Time</div>
			<div id="indoor-temp" class="massive-txt">69&degF</div>
		</div>
		<div id="right-wrapper" class="col-3 ctr">
			<div id="desired-temp-wrapper" class="lg-txt">
				<span id="desired-temp-lable">Desired Temp: </span>
				<span id="desired-temp"></span>
			</div>
			<div id="control-btns">
				<div id="up-button">
					<img id="adj-up-image" src="../assets/images/icons/up-arrow.png" alt="adj-up" onclick="onTempUp()"></img>
				</div>
				<div id="down-button">
				<img id="adj-down-image" src="../assets/images/icons/down-arrow.png" alt="adj-down" onclick="onTempDown()"></img>
				</div>
			</div>
		</div>
	</body>
</html>
