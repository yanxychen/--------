import { AssetTypeMatcher } from '../src';

const matcher = new AssetTypeMatcher();

function example() {
  const testCases = [
    { title: '佛山市禅城区滨海御庭住宅拍卖', targetType: '住宅' },
    { title: '佛山市禅城区祖庙路商铺拍卖', targetType: '商业' },
    { title: '佛山市南海区工业园厂房拍卖', targetType: '工业' },
    { title: '佛山市顺德区住宅用地拍卖', targetType: '土地' },
    { title: '滨海御庭3栋201室', targetType: '住宅' },
  ];

  console.log('=== 资产类型匹配测试 ===\n');

  for (const testCase of testCases) {
    const result = matcher.match({
      title: testCase.title,
      buildingArea: 100,
      targetType: testCase.targetType,
    });

    console.log(`标题: ${testCase.title}`);
    console.log(`目标类型: ${testCase.targetType}`);
    console.log(`是否匹配: ${result.isMatch ? '✅' : '❌'}`);
    console.log(`匹配类型: ${result.matchedType}`);
    console.log(`子类型: ${result.matchedSubType || '无'}`);
    console.log(`置信度: ${result.confidence}%`);
    console.log(`原因: ${result.matchReason}`);
    console.log();
  }

  const detected = matcher.detectType('佛山市禅城区岭南天地写字楼拍卖');
  console.log('类型检测示例:');
  console.log(`  类型: ${detected.type}`);
  console.log(`  子类型: ${detected.subType || '无'}`);
  console.log(`  置信度: ${detected.confidence}%`);
}

example();
