<table width="100%" class="mainWindow">
<tr><td class="mainWindowHead">
<?php
echo '<p>Setup profile</p>';


if (get_get('subaction')) {
	session_set('subaction', get_get('subaction') );
}

if (get_get('pid')) {
	session_set('periode_pid', get_get('pid'));
}
//print "<p>Pid now: " . session_get('periode_pid');

if (get_get('tid')) {
	session_set('periode_tid', get_get('tid'));
}
//print "<p>Tid now: " . session_get('periode_tid');


$utstginfo = $dbh->brukerprofilInfo(session_get('periode_pid') );
echo '<div class="subheader">' . $utstginfo[0] . '</div>';

?>
</td></tr>

<tr><td>
<?php
include("loginordie.php");
loginOrDie();


echo '<p>';
echo gettext("To add a new time period, you have to click on the time you want the time period to start (on the time table below).");

// funksjonen returnerer "" eller " checked " avhengig om en dag er inkludert i 
// perioden, for bruk i endrePeriode

function getChecked($helg, $dag) {
	if ($dag == 0) // Mandag - Fredag
		if ($helg == 1 OR $helg == 2) return " checked ";
	if ($dag == 1) // Lørdag eller Søndag
		if ($helg == 1 OR $helg == 3) return " checked ";
	return "";
}

function helgdescr($helg) {
	switch($helg) {
		case 1 : return gettext('All week');
		case 2 : return gettext('Weekdays');
		case 3 : return gettext('Weekend');
		default: return gettext('Uknown');
	}
}

/* Funksjon som legger inn en boks hvor man kan endre på en tidsperiode. Denne
 * er nødvendig siden disse boksene kan dukke opp på forskjellige plasser.
 */
 
function endrePeriode($dbh) {

	// Hente ut info om periode
	$periodeinfo = $dbh->periodeInfo(session_get('periode_tid') );

	print "<form name=\"endre\" method=\"post\" action=\"index.php?subaction=endreperiode\">";
	print "<table width=\"100%\" class=\"endreboks\"><tr>";
	
	print "<td align=\"center\"><h2>Oppsett av varsling i tidsperiode</h2><p>Klokkeslett: ";
	print '<input name="time" type="text" id="time" value="' . 
		leading_zero($periodeinfo[1], 2, 0) . '" size="2" maxlength="2"> : ';
    print '<input name="min" type="text" id="min" value="' .
    	leading_zero($periodeinfo[2], 2, 0) . '" size="2" maxlength="2"></td></tr>  ';

	
	// Endre dagtype, helg eller hverdag
	print "<tr><td align=\"left\">";
	print '<input name="hverdag" type="checkbox"  value="t"' . 
		getChecked($periodeinfo[0], 0) . '>' . gettext("Monday - Friday") . '<br>'
		. '<input name="helg" type="checkbox"  value="t"' .
		getChecked($periodeinfo[0], 1) . '>' . gettext("Saturday and Sunday");
	print "</td></tr>";



	
	// Legge til utstyrsliste	
	$utst = new Lister( 107,
		array(gettext('Owner'), gettext('Equipment'), gettext('#periods'), gettext('#filters')),
		array(10, 60, 15, 15),
		array('center', 'left', 'left', 'left'),
		array(true, true, true, true),
		1);

	if ( get_exist('sortid') )
		$utst->setSort(get_get('sort'), get_get('sortid') );

	$ut = $dbh->listUtstyrPeriode(session_get('uid'),
			session_get('periode_tid'), session_get('periode_gid'),  $utst->getSort() );


	for ($i = 0; $i < sizeof($ut); $i++) {

		if ($ut[$i][4] == 't') {
			$min = "<img alf=\"Min\" src=\"icons/person1.gif\">"; 
		} else {
			$min = "<img alf=\"Gruppe\" src=\"icons/gruppe.gif\">";
		}

		if ($ut[$i][5] == 't') {
			$valgt = " checked";
		} else {
			$valgt = "";
		}

  		if ($ut[$i][2] > 0 ) { 
  			$ap = $ut[$i][2]; 
  		} else { 
  			$ap = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
  		}
    
    	if ($ut[$i][3] > 0 ) { 
    		$af = $ut[$i][3]; 
    	} else { 
    		$af = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; 
    	}
		
		$utst->addElement( array($min, // eier
  			$ut[$i][1], // navn
  			$ap, // antall perioder
  			$af  // antall filtre
  			) );
  
		$adr = $dbh->listVarsleAdresser(session_get('uid'), 
			session_get('periode_tid'), $ut[$i][0], 0);

		$adrt = '<table width="80%" align="right" border="0" cellpadding="0" cellspacing="0"  >';

		for ($j = 0; $j < sizeof($adr); $j++) {
                    $adrt .= '<tr><td>';
                    switch($adr[$j][2]) {
                        case 1 : $adrt .= '<img alt="ikon" src="icons/mail.gif" border=0>&nbsp;E-post'; break;
                        case 2 : $adrt .= '<img alt="ikon" src="icons/mobil.gif" border=0>&nbsp;SMS'; break;
                        case 3 : $adrt .= '<img alt="ikon" src="icons/irc.gif" border=0>&nbsp;IRC'; break;
                        case 4 : $adrt .= '<img alt="ikon" src="icons/icq.gif" border=0>&nbsp;ICQ'; break;				
                        default : $adrt .= '<img alt="ikon" src="" border=0>&nbsp;Ukjent'; break;				
                    }
                    $adrt .= '</td><td>';
                    
                    for ($ti = 0; $ti < 5; $ti++) { $chckd[$ti] = ""; }
                    if (isset($adr[$j][3]) ) {
                            $chckd[$adr[$j][3]] = " selected";
                    } else {
                            $chckd[4] = " selected";
                    }
                    $adrt .= '<select name="queue' . $ut[$i][0] . '-' . $adr[$j][0]. '">' . "\n";			
                    $adrt .= '<option value="4"' . $chckd[4] . '>' . gettext("No") . '</option>&nbsp;';
                    $adrt .= '<option value="0"' . $chckd[0] . '>' . gettext("Yes") . '</option>&nbsp;';		
                    if ($adr[$j][2] != 2) {
                        $adrt .= '<option value="1"' . $chckd[1] . '>' . gettext("Put in queue (flushed daily)") . '</option>&nbsp;';
                        $adrt .= '<option value="2"' . $chckd[2] . '>' . gettext("Put in queue (flushed weekly)") . '</option>&nbsp;';
                        $adrt .= '<option value="3"' . $chckd[3] . '>' . gettext("Put in queue (until profile change)") . '</option>&nbsp;' . "\n";
                    }

                    $adrt .= '</select>';

                    $adrt .= '</td><td>' . $adr[$j][1] . '</td></tr>';	
                    $adrt .= '</tr>';
		}			
  			
  		$adrt .= '</table>';
  		$utst->addElement(new HTMLCell($adrt) );


	}
	
	
	print "<tr><td><h3>" . gettext("Choose equipment to be supervised and setup alert types.") . "</h3>" . 
		$utst->getHTML() . "</td></tr>";
	
	print "<tr><td align=\"center\">";
	print '<input type="submit" name="Submit" value="' . gettext("Save changes") . '">  ';
	print "</td></tr></table>";
	print "</form>";
	
}



if (!$dbh->permissionProfile( session_get('uid'), session_get('periode_pid') ) ) {
    echo "<h2>Security violation</h2>";
    exit(0);
} 

if ( isset($coor1) OR isset($coor2) ) {

    if (isset($coor2)) {
        $dtype = 3; $coor=$coor2;
    } else {
        $dtype = 2; $coor=$coor1;
    }
    
  preg_match("/^\?[0-9]+,([0-9]+)$/i", $coor, $match);
  $units = round((($match[1]-10) / 7.5) + 12) % 48;
  $time = floor($units / 2);
  $min = ($units % 2) * 30; 
  if ($min > 9 ) $klokke = "$time:$min"; else
    $klokke = "$time:0$min";

  $tidsid = $dbh->nyTidsperiode($dtype, $klokke, session_get('periode_pid') );
  
  if ($tidsid > 0) { 
    print gettext("<p><font size=\"+3\">OK</font>, a new time periods is created. Go to the form below to setup alerts for this time period.");
	  session_set('subaction', "endre");
  } else {
    print "<p><font size=\"+3\">" . gettext('An error</font> occured, a new profile is <b>not</b> created."');
  }

  session_set('periode_tid', $tidsid);
  session_set('subaction', 'endre');
  
}


// Endre ting angående en periode både info, adresser og utstyrsgrupper
if (session_get('subaction') == 'endreperiode') {
	if (post_get('hverdag') == 't' AND post_get('helg') == 't') $helgv = 1;
	if (post_get('hverdag') != 't' AND post_get('helg') != 't') $helgv = 0;
	if (post_get('hverdag') == 't' AND post_get('helg') != 't') $helgv = 2;
	if (post_get('hverdag') != 't' AND post_get('helg') == 't') $helgv = 3;
	$dbh->endrePeriodeinfo(session_get('periode_tid'), $helgv, $time, $min);
	
	reset ($HTTP_POST_VARS);
	
	while ( list($n, $val) = each ($HTTP_POST_VARS)) {
		if ( preg_match("/queue([0-9]+)-([0-9]+)/i", $n, $m) ) {   // først utstyrsgruppeid så alarmadresseid
			$dbh->endreVarsleadresse(session_get('periode_tid'), $m[2], $m[1], $val);
		}
		
	}

	session_set('subaction',  'idle');
}


if (session_get('subaction') == 'slett' ) {

	if (session_get('periode_pid') > 0) { 
	
		$dbh->slettPeriode(session_get('periode_tid') );
		$adresse='';
		print "<p><font size=\"+3\">" . gettext("OK</font>, time period (") . session_get('periode_pid'). gettext(") is removed.");

	} else {
		print "<p><font size=\"+3\">" . gettext("An error</font> occured, the time period is <b>not</b> removed.");
	}

	// Viser feilmelding om det har oppstått en feil.
	if ( $error != NULL ) {
		print $error->getHTML();
		$error = NULL;
	}
	session_set('subaction', 'idle');
  
}


$konflikter = $dbh->listPeriodekonflikter(session_get('periode_pid'));
if (sizeof($konflikter) > 0) {
    $kl = new Lister (423,
                array('Dagtype', 'Tid', 'Antall kolliderende tidsperioder'),
                array(30, 20, 50),
                array('left', 'left', 'left'),
                array(false, false, false),
                0
    );
    for ($i = 0; $i < sizeof($konflikter); $i++) {
        $kl->addElement( array($konflikter[$i][1],$konflikter[$i][2],$konflikter[$i][0])  );
    }
    echo '<p><table width="100%"><tr><td><img alt="Warning" align="top" src="images/warning.png"></td><td>';
    echo '<h2>' . gettext("Conflicts") . '</h2>';
    echo '<p>' . gettext("You have setup two or more time periods in which starts at the same time. Remove or change some of the time periods causing the conflict and this warning will go away.");
    echo '<p>' . gettext("Here is a list of occuring conflicts:");

    echo $kl->getHTML();

    echo  '</td></tr></table>'; 

}




// dette er for hverdager mandag til fredag
$l[0] = new Lister( 108,
		array(gettext('Time'), gettext('Weekday'), gettext('#addresses'), 
			gettext('#equip grp.'), gettext('Options..') ),
		array(20, 20, 20, 20, 20),
		array('right', 'center', 'right', 'right', 'right'),
		array(true, false, false, false, false),
		0
	);


// dette er tabellen for helga, lørdag og søndag
$l[1] = new Lister( 109,
		array(gettext('Time'), gettext('Weekday'), gettext('#addresses'), 
			gettext('#equip. grp.'), gettext('Options..') ),
		array(20, 20, 20, 20, 20),
		array('right', 'center', 'right', 'right', 'right'),
		array(true, false, false, false, false),
		0
	);

if ( get_exist('sortid') ) {
	$l[0]->setSort(get_get('sort'), get_get('sortid') );
	$l[1]->setSort(get_get('sort'), get_get('sortid') );	
}

$perioder = $dbh->listPerioder(session_get('periode_pid'), $l[0]->getSort() );

for ($i = 0; $i < sizeof($perioder); $i++) {

  if ($perioder[$i][2] > 9) $t = $perioder[$i][2]; else $t = "0" . $perioder[$i][2];
  if ($perioder[$i][3] > 9) $m = $perioder[$i][3]; else $m = "0" . $perioder[$i][3];
  $klokke = "$t:$m";
  $valg = '<a href="index.php?subaction=endre&tid=' . $perioder[$i][0] . 
  	'#endre"><img alt="Open" src="icons/open2.gif" border=0></a>&nbsp;' .
  	'<a href="index.php?subaction=slett&tid=' . $perioder[$i][0] . '">' .
    '<img alt="Delete" src="icons/delete.gif" border=0></a>';

  if ($perioder[$i][4] > 0 ) 
    { $aa = $perioder[$i][4]; }
  else 
    { $aa = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; }

  if ($perioder[$i][5] > 0 ) 
    { $au = $perioder[$i][5]; }
  else 
    { $au = "<img alt=\"Ingen\" src=\"icons/stop.gif\">"; }

  // mangdag til fredag
  if (($perioder[$i][1] == 1) OR ($perioder[$i][1] == 2)) {
    $l[0]->addElement( array($klokke,
    			helgdescr($perioder[$i][1] ),
			     $aa,  // # adresser
			     $au,  // # utstyrsgrupper
			     $valg
			     ) 
		       );
    $kt[0][] = array($perioder[$i][2], $perioder[$i][3]);
  }

  // lørdag og søndag
  if (($perioder[$i][1] == 1) OR ($perioder[$i][1] == 3)) {
    $l[1]->addElement( array($klokke,
    			helgdescr($perioder[$i][1] ),    
			     $aa,  // # adresser
			     $au,  // # utstyrsgrupper
			     $valg
			     ) 
		       );
    $kt[1][] = array($perioder[$i][2], $perioder[$i][3]);
  }
}

print "<h3>" . gettext("Monday - Friday") . "</h3>";
print "<table width=\"100%\"><tr><td>\n";
print "<A HREF=\"index.php?pid=$pid&coor1=\">\n";
print "<img border=\"0\" class=\"ilink\" alt=\"Timeplan Man-Fre\" src=\"timeplan.php?";
$c = 0;
foreach ($kt[0] as $el) {
     print "t[" . $c . "]=" . $kt[0][$c][0] . "&m[" . $c . "]=" . $kt[0][$c++][1] . "&";
}
print "\" ISMAP></A></td><td valign=\"top\">";
$tabell = $l[0]->getHTML();
echo $tabell;
print "</td></tr></table>";

if (session_get('subaction') == 'endre'  ) {
	print '<a name="endre">';
	endrePeriode($dbh, session_get('periode_tid') );
	//session_set('subaction', 'idle');
}

print "<h3>" . gettext("Saturday and Sunday") . "</h3>";
print '<table width="100%"><tr><td>';
print "<A HREF=\"index.php?pid=$pid&coor2=\"><img border=\"0\" class=\"ilink\" alt=\"Timeplan Lør-Søn\" src=\"timeplan.php?";
$c = 0;
foreach ($kt[1] as $el) {
     print "t[" . $c . "]=" . $kt[1][$c][0] . "&m[" . $c . "]=" . $kt[1][$c++][1] . "&";
}
print '" ISMAP></A></td><td valign="top">';
print $l[1]->getHTML();
print '</td></tr></table>';

print "<p>[ <a href=\"index.php\">" . gettext("update") . "<img src=\"icons/refresh.gif\" alt=\"oppdater\" border=\"0\"> ]</a> ";
print gettext("Number of periods: ") . sizeof($perioder);


echo '<p><form name="finnished" method="post" action="index.php?action=profil">';
echo '<input align="right" type="submit" name="Submit" value="' . gettext('Finished setting up profile') . '">';
echo '</form>';

?>

</td></tr>
</table>
