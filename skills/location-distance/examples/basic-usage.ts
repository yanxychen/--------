import { LocationDistance } from '../src';

const locator = new LocationDistance({
  amapKey: 'your-amap-api-key-here',
});

async function example() {
  const address = '佛山市禅城区季华路滨海御庭1座';

  const { location, keywords } = await locator.locateAndExtract(address);

  if (location) {
    console.log('经纬度:', location.longitude, location.latitude);
    console.log('城市:', location.city);
    console.log('区域:', location.district);
  }

  console.log('分层关键词:', keywords);

  const p1 = { lng: 113.1234, lat: 23.1234 };
  const p2 = { lng: 113.2345, lat: 23.2345 };

  const straightDist = locator.haversineDistance(p1, p2);
  console.log('直线距离:', straightDist, '米');

  const drivingResult = await locator.drivingDistance(p1, p2);
  console.log('驾车距离:', drivingResult.drivingDistance, '米');
  console.log('驾车时间:', drivingResult.drivingDuration, '秒');
}

example().catch(console.error);
